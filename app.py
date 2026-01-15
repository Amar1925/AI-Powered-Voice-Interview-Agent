import streamlit as st
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import threading
import time
import io
import re
from enhanced_speech_handler import SpeechHandler

class InterviewAgent:
    def __init__(self):
        self.questions_db = {
            "Plumber": {
                "easy": [
                    "What is the main purpose of a P-trap in plumbing?",
                    "What tools do you commonly use for basic pipe repairs?",
                    "How do you turn off the main water supply?",
                    "What's the difference between hot and cold water pipes?",
                    "What should you do if you find a small water leak?"
                ],
                "medium": [
                    "How would you diagnose a running toilet problem?",
                    "Explain the process of installing a new faucet.",
                    "What causes low water pressure and how do you fix it?",
                    "How do you properly join copper pipes?",
                    "What are the signs of a failing water heater?"
                ],
                "hard": [
                    "Explain the hydraulic principles behind water hammer and its solutions.",
                    "How would you design a drainage system for a multi-story building?",
                    "What are the code requirements for backflow prevention systems?",
                    "How do you calculate pipe sizing for a commercial building?",
                    "Explain the process of hydro jetting and when it's appropriate."
                ]
            },
            "Electrician": {
                "easy": [
                    "What is the purpose of a circuit breaker?",
                    "What's the difference between AC and DC current?",
                    "What tools do you need for basic electrical work?",
                    "What safety precautions should you take before working on electrical systems?",
                    "What does grounding mean in electrical systems?"
                ],
                "medium": [
                    "How do you wire a three-way switch?",
                    "What causes electrical outlets to stop working?",
                    "Explain how to install a ceiling fan with proper wiring.",
                    "What are GFCI outlets and where are they required?",
                    "How do you troubleshoot a circuit that keeps tripping?"
                ],
                "hard": [
                    "Explain three-phase power systems and their applications.",
                    "How do you design electrical load calculations for a building?",
                    "What are the NEC requirements for electrical panel installations?",
                    "How do you troubleshoot motor control circuits?",
                    "Explain power factor correction and its importance."
                ]
            }
        }
        
        # Scoring keywords for each job type
        self.scoring_keywords = {
            "Plumber": {
                "easy": {
                    "high_value": ["trap", "sewer", "gas", "prevent", "water", "drain", "pipe"],
                    "medium_value": ["plumbing", "tools", "wrench", "valve", "supply", "leak", "repair"],
                    "basic_value": ["turn", "off", "main", "hot", "cold", "fix", "check"]
                },
                "medium": {
                    "high_value": ["diagnose", "flapper", "chain", "installation", "pressure", "copper", "solder", "temperature"],
                    "medium_value": ["toilet", "faucet", "valve", "joint", "pipe", "water", "heater", "flow"],
                    "basic_value": ["running", "install", "low", "join", "signs", "failing", "problem"]
                },
                "hard": {
                    "high_value": ["hydraulic", "water hammer", "arrestor", "drainage", "code", "backflow", "prevention", "calculation", "hydro jetting"],
                    "medium_value": ["principles", "design", "building", "requirements", "sizing", "commercial", "process"],
                    "basic_value": ["explain", "solutions", "system", "appropriate", "when", "why"]
                }
            },
            "Electrician": {
                "easy": {
                    "high_value": ["circuit breaker", "overload", "protection", "AC", "DC", "current", "alternating", "direct", "grounding", "safety"],
                    "medium_value": ["electrical", "tools", "multimeter", "wire", "voltage", "safety", "precautions"],
                    "basic_value": ["purpose", "difference", "work", "take", "mean", "systems"]
                },
                "medium": {
                    "high_value": ["three-way switch", "traveler", "GFCI", "ground fault", "troubleshoot", "circuit", "tripping"],
                    "medium_value": ["wire", "outlets", "ceiling fan", "installation", "electrical", "power"],
                    "basic_value": ["causes", "install", "required", "working", "problem"]
                },
                "hard": {
                    "high_value": ["three-phase", "power systems", "load calculations", "NEC", "motor control", "power factor", "correction"],
                    "medium_value": ["design", "electrical", "building", "requirements", "panel", "installations", "circuits"],
                    "basic_value": ["explain", "applications", "troubleshoot", "importance"]
                }
            }
        }
        
        self.interview_data = {
            "job_type": "",
            "questions": [],
            "answers": [],
            "difficulty_levels": [],
            "scores": [],
            "start_time": None,
            "end_time": None
        }
        
        self.current_difficulty = "medium"
        self.question_count = 0
        self.max_questions = 5
        
        # Initialize enhanced speech handler
        self.speech_handler = SpeechHandler()
        
    def calculate_answer_score(self, answer, difficulty):
        """Calculate score for an answer based on keywords and quality"""
        if not answer or answer.lower() in ["skipped", "timeout", "unclear", "no_speech_detected"]:
            return 0
        
        answer_lower = answer.lower()
        job_keywords = self.scoring_keywords.get(self.interview_data["job_type"], {}).get(difficulty, {})
        
        # Count keyword matches
        high_value_matches = sum(1 for keyword in job_keywords.get("high_value", []) if keyword in answer_lower)
        medium_value_matches = sum(1 for keyword in job_keywords.get("medium_value", []) if keyword in answer_lower)
        basic_value_matches = sum(1 for keyword in job_keywords.get("basic_value", []) if keyword in answer_lower)
        
        # Calculate base score from keywords
        keyword_score = (high_value_matches * 3) + (medium_value_matches * 2) + (basic_value_matches * 1)
        
        # Adjust score based on answer length and completeness
        word_count = len(answer.split())
        length_multiplier = min(1.0, word_count / 20)  # Optimal around 20 words
        
        # Calculate final score (0-10)
        base_score = min(10, keyword_score * length_multiplier)
        
        # Bonus for comprehensive answers
        if word_count > 30 and high_value_matches > 0:
            base_score = min(10, base_score + 1)
        
        # Difficulty adjustment
        difficulty_multipliers = {"easy": 0.8, "medium": 1.0, "hard": 1.2}
        final_score = min(10, base_score * difficulty_multipliers.get(difficulty, 1.0))
        
        return round(final_score, 1)
    
    def evaluate_answer_quality(self, answer):
        """Enhanced answer quality evaluation"""
        if not answer or len(answer.strip()) < 10:
            return "poor"
        
        score = self.calculate_answer_score(answer, self.current_difficulty)
        
        if score >= 7:
            return "good"
        elif score >= 4:
            return "average"
        else:
            return "poor"
    
    def adjust_difficulty(self, answer_quality):
        """Adjust difficulty based on answer quality"""
        if answer_quality == "good" and self.current_difficulty != "hard":
            if self.current_difficulty == "easy":
                self.current_difficulty = "medium"
            else:
                self.current_difficulty = "hard"
        elif answer_quality == "poor" and self.current_difficulty != "easy":
            if self.current_difficulty == "hard":
                self.current_difficulty = "medium"
            else:
                self.current_difficulty = "easy"
    
    def get_next_question(self):
        """Get next question based on current difficulty"""
        if self.question_count >= self.max_questions:
            return None
        
        questions = self.questions_db[self.interview_data["job_type"]][self.current_difficulty]
        question = questions[self.question_count % len(questions)]
        return question
    
    def speak_text_threaded(self, text):
        """Convert text to speech with proper error handling"""
        try:
            # Reset TTS engine before speaking
            self.speech_handler.reset_tts_engine()
            
            # Use synchronous speech for better reliability
            self.speech_handler.speak_text(text)
            
        except Exception as e:
            st.error(f"TTS Error: {str(e)}")
            # Try reinitializing the speech handler
            try:
                self.speech_handler = SpeechHandler()
                self.speech_handler.speak_text(text)
            except Exception as e2:
                st.error(f"TTS Reinit Error: {str(e2)}")
    
    def listen_for_speech(self, timeout=20):
        """Enhanced speech recognition with better pause handling"""
        return self.speech_handler.listen_for_speech_with_pauses(
            timeout=timeout, 
            max_pause_duration=3.0
        )
    
    def calculate_overall_score(self):
        """Calculate overall interview score"""
        if not self.interview_data["scores"]:
            return 0
        
        total_score = sum(self.interview_data["scores"])
        max_possible = len(self.interview_data["scores"]) * 10
        percentage = (total_score / max_possible) * 100 if max_possible > 0 else 0
        
        return {
            "total_points": total_score,
            "max_possible": max_possible,
            "percentage": round(percentage, 1),
            "grade": self.get_grade(percentage),
            "average_per_question": round(total_score / len(self.interview_data["scores"]), 1)
        }
    
    def get_grade(self, percentage):
        """Convert percentage to letter grade"""
        if percentage >= 90:
            return "A+"
        elif percentage >= 80:
            return "A"
        elif percentage >= 70:
            return "B"
        elif percentage >= 60:
            return "C"
        elif percentage >= 50:
            return "D"
        else:
            return "F"
    
    def generate_pdf_report(self):
        """Generate enhanced PDF report with scoring"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.darkblue,
            spaceAfter=30,
            alignment=1
        )
        story.append(Paragraph("Interview Assessment Report", title_style))
        
        # Calculate overall score
        score_data = self.calculate_overall_score()
        
        # Interview details with scoring
        details = [
            ["Job Type:", self.interview_data["job_type"]],
            ["Date:", datetime.now().strftime("%Y-%m-%d")],
            ["Duration:", f"{(self.interview_data['end_time'] - self.interview_data['start_time']).seconds // 60} minutes"],
            ["Questions Asked:", str(len(self.interview_data["questions"]))],
            ["Overall Score:", f"{score_data['total_points']}/{score_data['max_possible']} ({score_data['percentage']}%)"],
            ["Grade:", score_data['grade']],
            ["Average per Question:", f"{score_data['average_per_question']}/10"]
        ]
        
        detail_table = Table(details, colWidths=[2*inch, 4*inch])
        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        
        story.append(detail_table)
        story.append(Spacer(1, 20))
        
        # Performance Analysis
        story.append(Paragraph("Performance Analysis", styles['Heading2']))
        performance_text = f"""
        <b>Overall Performance:</b> {score_data['grade']} ({score_data['percentage']}%)<br/>
        <b>Strengths:</b> {'Good technical knowledge' if score_data['percentage'] > 70 else 'Room for improvement in technical areas'}<br/>
        <b>Areas for Improvement:</b> {'Continue building on strong foundation' if score_data['percentage'] > 70 else 'Focus on technical terminology and detailed explanations'}
        """
        story.append(Paragraph(performance_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Score breakdown table
        score_breakdown = [["Question", "Difficulty", "Score", "Answer Quality"]]
        for i, (score, difficulty) in enumerate(zip(self.interview_data["scores"], self.interview_data["difficulty_levels"])):
            quality = "Excellent" if score >= 8 else "Good" if score >= 6 else "Average" if score >= 4 else "Poor"
            score_breakdown.append([f"Q{i+1}", difficulty.title(), f"{score}/10", quality])
        
        score_table = Table(score_breakdown, colWidths=[1*inch, 1.5*inch, 1*inch, 1.5*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Score Breakdown", styles['Heading3']))
        story.append(score_table)
        story.append(Spacer(1, 20))
        
        # Questions and answers
        story.append(Paragraph("Interview Questions & Answers", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        for i, (question, answer, difficulty, score) in enumerate(zip(
            self.interview_data["questions"], 
            self.interview_data["answers"],
            self.interview_data["difficulty_levels"],
            self.interview_data["scores"]
        )):
            # Question with score
            story.append(Paragraph(f"<b>Question {i+1} (Difficulty: {difficulty.title()}) - Score: {score}/10</b>", styles['Normal']))
            story.append(Paragraph(question, styles['Normal']))
            story.append(Spacer(1, 6))
            
            # Answer
            story.append(Paragraph("<b>Answer:</b>", styles['Normal']))
            story.append(Paragraph(answer, styles['Normal']))
            story.append(Spacer(1, 12))
        
        doc.build(story)
        buffer.seek(0)
        return buffer

def main():
    st.set_page_config(
        page_title="AI Interview Agent",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 AI Interview Agent with Smart Scoring")
    st.markdown("An intelligent interviewing system with dynamic difficulty adjustment and comprehensive scoring")
    
    # Initialize session state
    if 'agent' not in st.session_state:
        st.session_state.agent = InterviewAgent()
    if 'interview_started' not in st.session_state:
        st.session_state.interview_started = False
    if 'interview_completed' not in st.session_state:
        st.session_state.interview_completed = False
    if 'current_question' not in st.session_state:
        st.session_state.current_question = None
    if 'speech_answer' not in st.session_state:
        st.session_state.speech_answer = ""
    if 'is_listening' not in st.session_state:
        st.session_state.is_listening = False
    if 'listening_status' not in st.session_state:
        st.session_state.listening_status = ""
    
    agent = st.session_state.agent
    
    # Job Selection
    if not st.session_state.interview_started:
        st.header("Step 1: Select Job Type")
        job_type = st.selectbox(
            "Which job are you applying for?",
            ["", "Plumber", "Electrician"],
            help="Select the job type you want to be interviewed for"
        )
        
        # Microphone test
        if st.button("🎤 Test Microphone"):
            if agent.speech_handler.test_microphone():
                st.success("✅ Microphone is working properly!")
            else:
                st.error("❌ Microphone test failed. Please check your microphone.")
        
        if job_type and st.button("Start Interview", type="primary"):
            agent.interview_data["job_type"] = job_type
            agent.interview_data["start_time"] = datetime.now()
            st.session_state.interview_started = True
            st.session_state.current_question = agent.get_next_question()
            st.rerun()
    
    # Interview Process
    elif st.session_state.interview_started and not st.session_state.interview_completed:
        st.header(f"Interview for {agent.interview_data['job_type']}")
        
        # Progress bar
        progress = agent.question_count / agent.max_questions
        st.progress(progress, text=f"Question {agent.question_count + 1} of {agent.max_questions}")
        
        if st.session_state.current_question:
            st.subheader(f"Question {agent.question_count + 1} (Difficulty: {agent.current_difficulty.title()})")
            st.write(st.session_state.current_question)
            
            # TTS Button with improved error handling
            if st.button("🔊 Listen to Question"):
                with st.spinner("Speaking question..."):
                    try:
                        agent.speak_text_threaded(st.session_state.current_question)
                        st.success("Question is being spoken! 🔊")
                    except Exception as e:
                        st.error(f"TTS Error: {e}")
            
            # Answer input methods
            st.subheader("Your Answer:")
            
            # Create columns for speech and text input
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**Option 1: Enhanced Speech Input**")
                
                # Speech to text button
                if st.button("🎤 Start Speaking (Enhanced)", key="speech_button"):
                    st.session_state.is_listening = True
                    st.session_state.listening_status = "Listening... Speak clearly and take natural pauses."
                    
                if st.session_state.is_listening:
                    status_placeholder = st.empty()
                    status_placeholder.info(st.session_state.listening_status)
                    
                    with st.spinner("🎤 Listening for up to 15 seconds... Speak now!"):
                        speech_result = agent.listen_for_speech(timeout=15)
                        st.session_state.speech_answer = speech_result
                        st.session_state.is_listening = False
                        st.session_state.listening_status = ""
                        status_placeholder.empty()
                        st.rerun()
                
                # Display speech result
                if st.session_state.speech_answer:
                    if st.session_state.speech_answer not in ["timeout", "unclear", "no_speech_detected"]:
                        st.text_area(
                            "Speech recognized:",
                            value=st.session_state.speech_answer,
                            height=100,
                            key=f"speech_display_{agent.question_count}",
                            disabled=True
                        )
                        
                        if st.button("✅ Use Speech Answer", key="use_speech"):
                            final_answer = st.session_state.speech_answer
                            _process_answer(agent, final_answer)
                    else:
                        st.warning(f"Speech recognition result: {st.session_state.speech_answer}")
                        st.session_state.speech_answer = ""
            
            with col2:
                st.write("**Option 2: Text Input**")
                
                # Text input
                text_answer = st.text_area(
                    "Type your answer:",
                    height=100,
                    key=f"text_answer_{agent.question_count}"
                )
                
                if st.button("✅ Submit Text Answer", key="submit_text"):
                    if text_answer.strip():
                        _process_answer(agent, text_answer)
                    else:
                        st.error("Please provide an answer before submitting.")
            
            # Skip question option
            st.markdown("---")
            if st.button("⏭️ Skip Question"):
                _process_answer(agent, "Skipped")
    
    # Interview Completed
    elif st.session_state.interview_completed:
        st.header("🎉 Interview Completed!")
        st.success(f"Thank you for completing the {agent.interview_data['job_type']} interview!")
        
        # Calculate overall score
        score_data = agent.calculate_overall_score()
        
        # Interview Summary with enhanced scoring
        st.subheader("Interview Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Questions Asked", len(agent.interview_data["questions"]))
        with col2:
            duration = (agent.interview_data["end_time"] - agent.interview_data["start_time"]).seconds
            st.metric("Duration", f"{duration // 60}m {duration % 60}s")
        with col3:
            st.metric("Overall Score", f"{score_data['total_points']}/{score_data['max_possible']}")
        with col4:
            st.metric("Grade", f"{score_data['grade']} ({score_data['percentage']}%)")
        
        # Score visualization
        st.subheader("Performance Analysis")
        
        # Create score chart data
        import pandas as pd
        score_df = pd.DataFrame({
            'Question': [f"Q{i+1}" for i in range(len(agent.interview_data["scores"]))],
            'Score': agent.interview_data["scores"],
            'Difficulty': agent.interview_data["difficulty_levels"]
        })
        
        st.bar_chart(score_df.set_index('Question')['Score'])
        
        # Detailed scoring breakdown
        st.subheader("Detailed Score Breakdown")
        score_table_data = []
        for i, (question, answer, difficulty, score) in enumerate(zip(
            agent.interview_data["questions"], 
            agent.interview_data["answers"],
            agent.interview_data["difficulty_levels"],
            agent.interview_data["scores"]
        )):
            quality = "Excellent" if score >= 8 else "Good" if score >= 6 else "Average" if score >= 4 else "Poor"
            score_table_data.append({
                "Question": f"Q{i+1}",
                "Difficulty": difficulty.title(),
                "Score": f"{score}/10",
                "Quality": quality
            })
        
        st.dataframe(score_table_data, use_container_width=True)
        
        # Performance feedback
        if score_data['percentage'] >= 80:
            st.success("🌟 Excellent performance! You demonstrate strong technical knowledge and communication skills.")
        elif score_data['percentage'] >= 60:
            st.info("👍 Good performance! With some additional preparation, you'll be well-prepared for the role.")
        else:
            st.warning("📚 Consider reviewing technical concepts for this field to improve your interview performance.")
        
        # Display Q&A Summary
        with st.expander("View Complete Interview Details"):
            for i, (question, answer, difficulty, score) in enumerate(zip(
                agent.interview_data["questions"], 
                agent.interview_data["answers"],
                agent.interview_data["difficulty_levels"],
                agent.interview_data["scores"]
            )):
                st.write(f"**Q{i+1} ({difficulty.title()}) - Score: {score}/10**")
                st.write(f"**Question:** {question}")
                st.write(f"**Answer:** {answer}")
                st.write("---")
        
        # Generate PDF Report
        if st.button("📄 Generate PDF Report", type="primary"):
            with st.spinner("Generating comprehensive report..."):
                pdf_buffer = agent.generate_pdf_report()
                
                st.download_button(
                    label="📥 Download Interview Report with Scoring",
                    data=pdf_buffer.getvalue(),
                    file_name=f"{agent.interview_data['job_type']}_Interview_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
        
        # Start New Interview
        if st.button("🔄 Start New Interview"):
            # Reset everything
            st.session_state.agent = InterviewAgent()
            st.session_state.interview_started = False
            st.session_state.interview_completed = False
            st.session_state.current_question = None
            st.session_state.speech_answer = ""
            st.session_state.is_listening = False
            st.session_state.listening_status = ""
            st.rerun()

def _process_answer(agent, final_answer):
    """Helper function to process answers and move to next question"""
    # Calculate score for the answer
    score = agent.calculate_answer_score(final_answer, agent.current_difficulty)
    
    # Store question, answer, and score
    agent.interview_data["questions"].append(st.session_state.current_question)
    agent.interview_data["answers"].append(final_answer)
    agent.interview_data["difficulty_levels"].append(agent.current_difficulty)
    agent.interview_data["scores"].append(score)
    
    # Evaluate answer and adjust difficulty
    quality = agent.evaluate_answer_quality(final_answer)
    agent.adjust_difficulty(quality)
    
    # Move to next question
    agent.question_count += 1
    st.session_state.speech_answer = ""
    st.session_state.listening_status = ""
    
    if agent.question_count >= agent.max_questions:
        agent.interview_data["end_time"] = datetime.now()
        st.session_state.interview_completed = True
        st.rerun()
    else:
        st.session_state.current_question = agent.get_next_question()
        st.rerun()

if __name__ == "__main__":
    main()