# 🎙️ AI-Powered Voice Interview Agent

This repository contains an **AI-powered voice-based interview system** that dynamically conducts interviews, evaluates candidate responses, adjusts question difficulty in real time, and generates detailed performance reports.  
The project integrates **speech recognition, text-to-speech, Generative AI, and PDF reporting** using modern AI frameworks.

---

## 🚀 Features

- 🎤 **Voice-based Interview** (Speech-to-Text)
- 🔊 **Text-to-Speech** for questions (Google TTS / pyttsx3 / Piper fallback)
- 🧠 **Dynamic Difficulty Adjustment** based on answer quality
- 📊 **Automated Scoring & Grading System**
- 📄 **PDF Interview Report Generation**
- 🧩 **Multiple Job Roles Supported** (Plumber, Electrician)
- 📑 **AI-powered PDF Summarization API** using Gemini
- ⚙️ **Modular Architecture** (Streamlit + FastAPI)

---

## 📂 Project Structure
├── app.py # Streamlit UI for AI Interview Agent \
├── enhanced_speech_handler.py # Speech Recognition + TTS Engine \
├── main.py # FastAPI backend for PDF summarization (Gemini) \
├── requirements.txt # Python dependencies \
├── README.md # Project documentation \
└── .env # Environment variables (not committed) \

---

## 🧠 Technologies Used

- **Python**
- **Streamlit** – Frontend UI
- **FastAPI** – Backend API
- **SpeechRecognition** – Speech-to-Text
- **pyttsx3 / Google TTS / Piper** – Text-to-Speech
- **Google Gemini 2.0 Flash** – Generative AI
- **LangChain** – PDF loading & processing
- **ReportLab** – PDF generation
- **Pandas** – Data analysis
- **Groq / LangGraph (experimental)** – Agent workflows

---

## 🔧 Installation & Setup

### 1️⃣ Clone the repository
```bash
git clone https://github.com/your-username/AI-Powered-Voice-Interview-Agent.git
cd AI-Powered-Voice-Interview-Agent
```

### 2️⃣ Create and Activate a Virtual Environment

Create a virtual environment:
```bash
python -m venv venv
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 🔐 Environment Variables

Create a .env file in the root directory and add the following:

GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here


### ▶️ Running the Applications
```bash
streamlit run app.py
```

### Working Application should look like this
<img width="1919" height="950" alt="image" src="https://github.com/user-attachments/assets/645af5ae-cb05-4213-96bc-970166e88cf0" />

