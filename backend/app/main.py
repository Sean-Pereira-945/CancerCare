from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routes import chat, diet, reports, symptoms, medications, trials, caregiver
from app.auth import router as auth_router

settings = get_settings()

app = FastAPI(
    title="CancerCare AI API",
    description="AI-powered cancer patient support platform — RAG chatbot, report parsing, diet planning, symptom tracking, and more.",
    version="1.0.0"
)

# CORS — allow frontend to call the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all route groups
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chatbot"])
app.include_router(diet.router, prefix="/api/diet", tags=["Diet"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(symptoms.router, prefix="/api/symptoms", tags=["Symptoms"])
app.include_router(medications.router, prefix="/api/medications", tags=["Medications"])
app.include_router(trials.router, prefix="/api/trials", tags=["Clinical Trials"])
app.include_router(caregiver.router, prefix="/api/caregiver", tags=["Caregiver"])


@app.get("/")
async def root():
    return {
        "status": "CancerCare AI is running",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
