from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import engine, DATABASE_URL, get_mongo
from app.models.db import Base
from app.routes import chat, diet, reports, symptoms, medications, trials, caregiver
from app.auth import router as auth_router
from sqlalchemy import text
import time
import uuid
import logging

settings = get_settings()
logger = logging.getLogger("cancercare.api")

# Keep automatic DDL only for local SQLite/dev to avoid unsafe schema drift in managed DBs.
if DATABASE_URL.startswith("sqlite") or settings.auto_create_tables:
    Base.metadata.create_all(bind=engine)

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
        "http://127.0.0.1:5173",
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
app.include_router(trials.router, prefix="/api/trials", tags=["References"])
app.include_router(caregiver.router, prefix="/api/caregiver", tags=["Caregiver"])


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["x-request-id"] = request_id
    response.headers["x-response-time-ms"] = str(elapsed_ms)
    logger.info(
        "request_id=%s method=%s path=%s status=%s elapsed_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


@app.get("/")
async def root():
    return {
        "status": "CancerCare AI is running",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    db_ok = False
    mongo_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    try:
        mongo = get_mongo()
        # Dummy fallback exposes dict-like behavior; real db has command/list_collection_names.
        if hasattr(mongo, "command"):
            mongo.command("ping")
        mongo_ok = True
    except Exception:
        mongo_ok = False

    deps = {
        "database": "ok" if db_ok else "error",
        "mongodb": "ok" if mongo_ok else "error",
        "groq_configured": bool(settings.groq_api_key),
        "gemini_configured": bool(settings.gemini_api_key),
    }
    overall = "healthy" if db_ok else "degraded"
    return {"status": overall, "dependencies": deps}
