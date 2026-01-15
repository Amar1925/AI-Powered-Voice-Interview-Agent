import speech_recognition as sr
import subprocess
import tempfile
import os
import threading
import time
from typing import Optional
import json
import io
import pygame
import requests
from urllib.parse import quote

class SpeechHandler:
    def __init__(self):
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # TTS initialization with thread safety
        self.tts_lock = threading.Lock()
        self.tts_engine = None
        
        # Initialize pygame mixer for audio playback
        try:
            pygame.mixer.init()
            self.pygame_available = True
        except:
            self.pygame_available = False
            print("Pygame not available, using system audio")
        
        # Improved recognition settings
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 2.0
        self.recognizer.operation_timeout = None
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 1.5
        
        # TTS Options (in order of preference)
        self.tts_options = {
            'google_free': True,    # Free Google Translate TTS
            'pyttsx3': True,        # Offline TTS
            'piper': self._check_piper_available()  # Local Piper TTS
        }
        
        # Initialize offline TTS as fallback
        self._init_pyttsx3()
        
        # Adjust for ambient noise
        self._calibrate_microphone()
    
    def _init_pyttsx3(self):
        """Initialize pyttsx3 engine with thread safety"""
        try:
            import pyttsx3
            if hasattr(self, 'tts_engine') and self.tts_engine is not None:
                try:
                    self.tts_engine.stop()
                    del self.tts_engine
                except:
                    pass
            
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
        except Exception as e:
            print(f"Failed to initialize pyttsx3: {e}")
            self.tts_engine = None

    def reset_tts_engine(self):
        """Reset TTS engine to ensure it's ready for next use"""
        with self.tts_lock:
            try:
                if self.tts_engine:
                    self.tts_engine.stop()
                    time.sleep(0.1)
                    self._init_pyttsx3()
            except Exception as e:
                print(f"TTS reset error: {e}")
                self.tts_engine = None
                self._init_pyttsx3()
    
    def _check_piper_available(self) -> bool:
        """Check if Piper TTS files are available"""
        return (os.path.exists("en_US-amy-medium.onnx") and 
                os.path.exists("en_US-amy-medium.onnx.json"))
    
    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        try:
            with self.microphone as source:
                print("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                print(f"Energy threshold set to: {self.recognizer.energy_threshold}")
        except Exception as e:
            print(f"Microphone calibration error: {e}")
    
    def speak_text(self, text: str) -> None:
        """Convert text to speech using the best available option"""
        success = False
        
        # Try Google TTS first (free)
        if self.tts_options['google_free'] and not success:
            success = self._speak_with_google_free(text)
        
        # Fallback to Piper if available
        if not success and self.tts_options['piper']:
            success = self._speak_with_piper(text)
        
        # Final fallback to pyttsx3
        if not success and self.tts_options['pyttsx3']:
            self._speak_with_pyttsx3(text)
    
    def _speak_with_google_free(self, text: str) -> bool:
        """Use Google Translate's free TTS service"""
        try:
            # Clean and prepare text
            text = text.strip()
            if len(text) > 200:  # Google Translate TTS has length limits
                text = text[:200] + "..."
            
            # Google Translate TTS URL (free service)
            encoded_text = quote(text)
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=en&client=tw-ob&q={encoded_text}"
            
            # Download audio
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Play audio using pygame or save to temp file
                if self.pygame_available:
                    # Load audio data into pygame
                    audio_data = io.BytesIO(response.content)
                    pygame.mixer.music.load(audio_data)
                    pygame.mixer.music.play()
                    
                    # Wait for playback to complete
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                    
                    return True
                else:
                    # Save to temp file and play
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                        temp_file.write(response.content)
                        temp_path = temp_file.name
                    
                    # Play the file
                    if os.name == 'nt':  # Windows
                        os.system(f'start /wait "" "{temp_path}"')
                    else:  # Linux/Mac
                        subprocess.run(['mpg123', temp_path], capture_output=True)
                    
                    # Clean up
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                    
                    return True
            else:
                print(f"Google TTS request failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Google TTS Error: {e}")
            return False
    
    def _speak_with_piper(self, text: str) -> bool:
        """Use Piper TTS for speech synthesis"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                temp_wav_path = temp_wav.name
            
            piper_cmd = f'echo "{text}" | piper --model en_US-amy-medium.onnx --config en_US-amy-medium.onnx.json --output_file {temp_wav_path}'
            result = subprocess.run(piper_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(temp_wav_path):
                if self.pygame_available:
                    pygame.mixer.music.load(temp_wav_path)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                else:
                    if os.name == 'nt':
                        os.system(f'start /wait "" "{temp_wav_path}"')
                    else:
                        subprocess.run(['aplay' if 'linux' in os.sys.platform else 'afplay', temp_wav_path])
                
                try:
                    os.unlink(temp_wav_path)
                except:
                    pass
                return True
            else:
                print(f"Piper TTS failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Piper TTS Error: {e}")
            return False
    
    def _speak_with_pyttsx3(self, text: str) -> None:
        """Fallback TTS using pyttsx3"""
        with self.tts_lock:
            try:
                if self.tts_engine is None:
                    self._init_pyttsx3()
                
                if self.tts_engine:
                    try:
                        self.tts_engine.stop()
                        time.sleep(0.1)
                    except:
                        pass
                    
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                    time.sleep(0.1)
                else:
                    print("TTS engine not available")
                    
            except Exception as e:
                print(f"pyttsx3 TTS Error: {e}")
                try:
                    self.tts_engine = None
                    time.sleep(0.2)
                    self._init_pyttsx3()
                    if self.tts_engine:
                        self.tts_engine.say(text)
                        self.tts_engine.runAndWait()
                except Exception as e2:
                    print(f"TTS reinit also failed: {e2}")
    
    def listen_for_speech_with_pauses(self, timeout: int = 20, max_pause_duration: float = 3.0) -> Optional[str]:
        """Enhanced speech recognition that handles pauses better"""
        try:
            print("Listening... Speak now! (I'll wait for natural pauses)")
            
            collected_audio = []
            last_speech_time = time.time()
            start_time = time.time()
            
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            while (time.time() - start_time) < timeout:
                try:
                    with self.microphone as source:
                        audio = self.recognizer.listen(
                            source,
                            timeout=1.0,
                            phrase_time_limit=5.0
                        )
                    
                    collected_audio.append(audio)
                    last_speech_time = time.time()
                    print("Audio detected, continuing to listen...")
                    
                except sr.WaitTimeoutError:
                    silence_duration = time.time() - last_speech_time
                    
                    if collected_audio and silence_duration > max_pause_duration:
                        print(f"Natural pause detected ({silence_duration:.1f}s), processing speech...")
                        break
                    elif not collected_audio and silence_duration > timeout / 2:
                        print("No speech detected for extended period")
                        return "timeout"
                    continue
                
                except Exception as e:
                    print(f"Audio capture error: {e}")
                    continue
            
            if not collected_audio:
                return "no_speech_detected"
            
            # Process collected audio
            print("Processing collected speech...")
            full_text_parts = []
            
            for audio_segment in collected_audio:
                try:
                    # Try Google Speech Recognition (free)
                    text = self.recognizer.recognize_google(audio_segment, language='en-US')
                    if text.strip():
                        full_text_parts.append(text.strip())
                        print(f"Recognized segment: {text}")
                except sr.UnknownValueError:
                    print("Could not understand audio segment")
                    continue
                except sr.RequestError as e:
                    print(f"Speech recognition service error: {e}")
                    # Try offline recognition as fallback
                    try:
                        text = self.recognizer.recognize_sphinx(audio_segment)
                        if text.strip():
                            full_text_parts.append(text.strip())
                            print(f"Recognized offline: {text}")
                    except:
                        continue
            
            if full_text_parts:
                full_text = " ".join(full_text_parts)
                print(f"Complete recognized text: {full_text}")
                return full_text
            else:
                return "unclear"
                
        except Exception as e:
            print(f"Speech recognition error: {e}")
            return f"error: {e}"
    
    def listen_for_speech(self, timeout: int = 15, phrase_timeout: int = 8) -> Optional[str]:
        """Listen for speech with improved recognition"""
        try:
            print("Listening... Speak now!")
            
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_timeout
                )
            
            print("Processing speech...")
            
            # Try Google Speech Recognition first (free)
            try:
                text = self.recognizer.recognize_google(audio, language='en-US')
                print(f"Recognized: {text}")
                return text
            except sr.UnknownValueError:
                print("Could not understand audio, trying alternative...")
                try:
                    text = self.recognizer.recognize_google(audio, language='en-IN')
                    print(f"Recognized (alternative): {text}")
                    return text
                except:
                    # Try offline recognition as last resort
                    try:
                        text = self.recognizer.recognize_sphinx(audio)
                        print(f"Recognized offline: {text}")
                        return text
                    except:
                        return "unclear"
                    
        except sr.WaitTimeoutError:
            print("No speech detected within timeout period")
            return "timeout"
        except sr.RequestError as e:
            print(f"Speech recognition service error: {e}")
            return f"service_error: {e}"
        except Exception as e:
            print(f"Unexpected error: {e}")
            return f"error: {e}"
    
    def test_microphone(self) -> bool:
        """Test if microphone is working"""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("Microphone test successful")
                return True
        except Exception as e:
            print(f"Microphone test failed: {e}")
            return False
    
    def get_available_microphones(self):
        """Get list of available microphones"""
        return sr.Microphone.list_microphone_names()
    
    def set_microphone(self, device_index: int):
        """Set specific microphone device"""
        try:
            self.microphone = sr.Microphone(device_index=device_index)
            self._calibrate_microphone()
            return True
        except Exception as e:
            print(f"Failed to set microphone: {e}")
            return False
    
    def set_tts_preference(self, google_free=True, pyttsx3=True, piper=None):
        """Set TTS preferences"""
        self.tts_options['google_free'] = google_free
        self.tts_options['pyttsx3'] = pyttsx3
        if piper is not None:
            self.tts_options['piper'] = piper