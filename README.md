# 🎗️ CancerCare AI

**AI-powered cancer patient support platform** — built with FastAPI, React, and LLMs.

## Features

- 💬 **RAG Chatbot** — AI assistant trained on medical knowledge + your personal reports
- 📋 **Report Parser** — Upload PDFs, extract cancer-related fields automatically
- 🥗 **Diet Engine** — Personalized 7-day meal plans based on cancer type & symptoms
- 📊 **Symptom Tracker** — Log daily symptoms with charts & mood sentiment analysis
- 💊 **Medication Manager** — Track medications, dosages, and schedules
- 🔬 **Clinical Trials** — Search recruiting trials from ClinicalTrials.gov
- 🤝 **Caregiver Portal** — Link to patients and monitor their health
- 🔐 **JWT Authentication** — Secure login/register with role-based access

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Tailwind CSS v4 (Vite) |
| Backend | FastAPI (Python 3.11) |
| LLMs | Gemini 1.5 Flash + Groq (Llama 3.1 70B) |
| NLP | HuggingFace Transformers |
| Vector DB | FAISS (local) |
| Primary DB | Supabase (PostgreSQL) |
| Document DB | MongoDB Atlas |
| Auth | JWT (bcrypt + python-jose) |

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables
Copy `.env` and fill in your API keys:
- `GEMINI_API_KEY` — from [Google AI Studio](https://aistudio.google.com)
- `GROQ_API_KEY` — from [Groq Console](https://console.groq.com)
- `SUPABASE_URL` / `SUPABASE_KEY` — from [Supabase](https://supabase.com)
- `MONGODB_URI` — from [MongoDB Atlas](https://cloud.mongodb.com)

## ⚕️ Medical Disclaimer
CancerCare AI is an educational tool providing general health information. It does NOT constitute medical advice, diagnosis, or treatment recommendations. Always consult your healthcare provider.
