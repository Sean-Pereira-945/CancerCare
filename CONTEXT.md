# CancerCare AI: Project Context

## 1. Project Mission
CancerCare AI is a high-fidelity clinical support platform designed to empower cancer patients and caregivers. It combines modern web technologies with advanced AI (RAG, NER, Sentiment Analysis) to provide personalized guidance, structured health tracking, and research-grade evaluation of medical AI interactions.

## 2. System Architecture

### Frontend (Vite + React)
- **Location**: `/frontend`
- **State Management**: TanStack React Query (v5+) for server state, standard React hooks for local state.
- **Styling**: Modern, responsive CSS with a focus on "Claymorphism" and accessibility.
- **Key Pages**:
    - `Home.jsx`: Public landing and entry point.
    - `Dashboard.jsx`: Central patient overview.
    - `Chatbot.jsx`: RAG-powered AI clinical assistant.
    - `Caregiver.jsx`: Specialized view for managing linked patient accounts.
    - `DietPlan.jsx`, `Medications.jsx`, `SymptomTracker.jsx`: Structured health management.

### Backend (FastAPI + Python)
- **Location**: `/backend`
- **Core Framework**: FastAPI for high-performance asynchronous API endpoints.
- **Authentication**: JWT-based secure auth system.
- **Database Layer**:
    - **Relational**: PostgreSQL (NeonDB) via SQLAlchemy 2.0. Handles core entities (Users, Logs, Meds).
    - **Document**: MongoDB for semi-structured clinical data.
    - **Vector**: FAISS for local semantic search and RAG retrieval.
- **API Clients**: Groq (primary LLM provider), Gemini (fallback/multimodal), Hugging Face (embeddings).

## 3. Core Intelligence Modules (`backend/app/ml/`)

| Module | Purpose |
|---|---|
| `rag_pipeline.py` | Core retrieval-augmented generation logic using FAISS. |
| `diet_engine.py` | Generates clinical-aware nutritional guidance. |
| `ner_extractor.py` | Named Entity Recognition for clinical report structured extraction. |
| `report_parser.py` | Multi-format (PDF/Text) report ingestion logic. |
| `sentiment.py` | Emotional well-being tracking from patient input. |
| `risk_model.py` | Basic heuristic-based symptom risk stratification. |

## 4. Research & Reproducibility (`research/`)
The repository includes a comprehensive setup for formal AI research:
- **Ablation Matrix**: Variants A0-A5 testing different RAG parameters.
- **LLM-as-a-Judge**: Using Llama-3.3-70B (via Groq) to evaluate response quality.
- **Statistical Analysis**: `statistical_analysis.py` performs bootstrap significance testing.
- **Visualization**: `generate_plots.py` creates publication-ready figures for research papers.

## 5. Recent Significant Changes
- **Supabase to NeonDB Migration**: Full refactor of the persistence layer to use SQLAlchemy with NeonDB, improving transaction handling and type safety.
- **TanStack Query v5 Integration**: Modernized frontend data fetching to eliminate manual `useEffect` fetches.
- **Experiment Runner v2**: Enhanced `experiment_runner.py` with resume-on-failure and rate-limit handling for Groq APIs.

## 6. Development Workflow
- **Backend Setup**: `python -m venv venv`, `pip install -r requirements.txt`, `uvicorn app.main:app`.
- **Frontend Setup**: `npm install`, `npm run dev`.
- **Unified Launch**: `run_project.bat` (Windows) starts both services concurrently.

---
*Note: This project is for educational/research purposes. Clinical advice should always be verified by professionals.*
