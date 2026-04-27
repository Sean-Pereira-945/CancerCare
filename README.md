# CancerCare AI

AI-powered cancer support platform with a FastAPI backend, React frontend, and LLM-powered clinical features.

## Core Features

- AI chatbot with RAG over medical references and uploaded patient reports
- Structured report parsing from uploaded documents
- Personalized diet planning support
- Symptom and sentiment tracking
- Medication tracking workflow
- Clinical trial lookup integration
- Caregiver/patient linking and role-aware access
- JWT authentication and protected routes

## Repository Structure

- `backend/`: FastAPI app, ML pipelines, database/auth routes, tests
- `frontend/`: Vite + React web UI
- `research/`: Evaluation scripts, datasets, and experiment assets
- `data/`: Local user report and vector-store data (ignored from Git)

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI (Python) |
| NLP/LLM | Hugging Face, Gemini, Groq |
| Vector Store | FAISS |
| Databases | PostgreSQL (Neon), MongoDB |
| Auth | JWT |

## Local Setup

### 1) Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3) Optional one-click launcher (Windows)

```bat
run_project.bat
```

## Environment Variables

Create `.env` files for backend/frontend as needed. Common backend variables include:

- `GEMINI_API_KEY`
- `GROQ_API_KEY`
- `MONGODB_URI`
- `NEON_POSTGRES_URL`
- `JWT_SECRET_KEY` (or equivalent auth secret used by your config)

## Testing

Backend tests:

```bash
cd backend
pytest
```

Frontend lint:

```bash
cd frontend
npm run lint
```
## Architecture Diagram 
```mermaid
flowchart LR
    U["Patient / Caregiver"] --> FE["Frontend\nReact + Vite\n[frontend/src/App.jsx]"]
    FE --> API["Backend API\nFastAPI\n[backend/app/main.py]"]

    API --> AUTH["Auth Layer\nJWT register/login/current user\n[backend/app/auth/router.py]"]
    API --> CHAT["Chat Route\n[backend/app/routes/chat.py]"]
    API --> REPORTS["Reports Route\n[backend/app/routes/reports.py]"]
    API --> DIET["Diet Route\n[backend/app/routes/diet.py]"]
    API --> SYM["Symptoms Route\n[backend/app/routes/symptoms.py]"]
    API --> MEDS["Medications Route\n[backend/app/routes/medications.py]"]
    API --> CARE["Caregiver Route\n[backend/app/routes/caregiver.py]"]
    API --> TRIALS["Trials Route\n[backend/app/routes/trials.py]"]

    AUTH --> SQL["SQL Database\nNeon/Postgres or SQLite fallback\n[backend/app/database.py]"]
    REPORTS --> SQL
    DIET --> SQL
    SYM --> SQL
    MEDS --> SQL
    CARE --> SQL

    REPORTS --> PARSER["Report Parser\nPyMuPDF + regex + LLM summary\n[backend/app/ml/report_parser.py]"]
    PARSER --> RISK["Risk Model\nPickled ML model\n[backend/app/ml/risk_model.py]"]
    PARSER --> USERFILES["User Report Files\n[data/user_reports/]"]
    PARSER --> USERVS["User Vector Store\nFAISS per user\n[data/vector_store/user_<id>/]"]

    CHAT --> RAG["RAG Pipeline\n[backend/app/ml/rag_pipeline.py]"]
    RAG --> GLOBALVS["Global Vector Store\nFAISS knowledge base\n[data/vector_store/]"]
    RAG --> USERVS
    GLOBALVS --> KB["Knowledge Base PDFs\n[data/knowledge_base/]"]

    CHAT --> GROQ["Groq LLM\nllama-3.3-70b-versatile"]
    DIET --> GROQ
    PARSER --> GROQ

    TRIALS --> CTGOV["ClinicalTrials.gov API"]

```
## Dataflow Diagram 
```mermaid
flowchart TD
    A["User logs in"] --> B["Frontend stores JWT\n[frontend/src/hooks/useAuth.jsx]"]
    B --> C["Frontend calls backend with Bearer token\n[frontend/src/lib/api.js]"]

    C --> D["Upload report PDF\n/api/reports/upload"]
    D --> E["Save original PDF to disk\n[data/user_reports/]"]
    D --> F["Parse PDF text\n[backend/app/ml/report_parser.py]"]
    F --> G["Extract fields with regex"]
    F --> H["Summarize with LLM"]
    G --> I["Save report metadata/text to SQL"]
    H --> I
    F --> J["Background index full text into user FAISS store"]

    C --> K["User asks chat question\n/api/chat/message"]
    K --> L["Load global FAISS knowledge base"]
    K --> M["Load user-specific FAISS report index"]
    L --> N["Retrieve top chunks"]
    M --> N
    N --> O["Assemble context"]
    O --> P["Compute retrieval confidence"]
    P --> Q{"Confidence high enough?"}

    Q -->|No| R["Return abstain/cautious response"]
    Q -->|Yes| S["Send prompt + context to Groq LLM"]
    S --> T["Return grounded answer + disclaimer"]

    C --> U["User logs symptoms / meals / meds"]
    U --> V["Persist structured tracking data in SQL"]
    V --> W["Dashboard queries trends and adherence"]

    X["Research dataset\n[research/datasets/eval_qa.jsonl]"] --> Y["Experiment runner\n[backend/experiment_runner.py]"]
    Y --> Z["Calls /api/chat/message for variants A0-A5"]
    Z --> AA["Collect response + context"]
    AA --> AB["LLM-as-judge scoring\n[backend/evaluation/metrics.py]"]
    AB --> AC["Raw results JSON\n[research/experiment_raw_data.json]"]
    AC --> AD["Aggregate CSV metrics\n[research/experiment_matrix.csv]"]
    AC --> AE["Statistical analysis\n[research/statistical_analysis.py]"]
    AD --> AF["Plots\n[research/generate_plots.py]"]

```

## Notes

- Large/generated assets (FAISS indexes, uploaded reports, caches) are excluded via `.gitignore`.
- Keep secrets out of version control.

## Medical Disclaimer

CancerCare AI is for educational and support purposes only and does not provide medical diagnosis or treatment advice. Always consult a licensed healthcare professional.
