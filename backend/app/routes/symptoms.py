from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Any
from app.auth.router import get_current_user
from app.database import get_db
from app.models.db import SymptomLog
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
import uuid

router = APIRouter()

class SymptomLogCreate(BaseModel):
    date: Optional[str] = None
    fatigue: int = Field(ge=1, le=10)
    nausea: int = Field(ge=1, le=10)
    pain: int = Field(ge=1, le=10)
    appetite: int = Field(ge=1, le=10)
    mood: int = Field(ge=1, le=10)
    sleep_hours: float = Field(ge=0, le=24)
    journal_text: Optional[str] = ""


def _parse_logged_at(date_str: Optional[str]) -> datetime:
    if not date_str:
        return datetime.utcnow()

    normalized = date_str.strip()
    if not normalized:
        return datetime.utcnow()

    if "T" in normalized:
        return datetime.fromisoformat(normalized.replace("Z", ""))

    # Accept plain date format (YYYY-MM-DD) and default to start of day.
    return datetime.fromisoformat(f"{normalized}T00:00:00")


def _coerce_mood(value: Any) -> int:
    text = str(value).strip() if value is not None else ""
    if text.isdigit():
        return int(text)
    return 5


def _coerce_symptoms(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}

@router.post("/log")
async def log_symptoms(data: SymptomLogCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Save daily symptom logs to the database."""
    # Map flat frontend data to the structured DB model
    symptoms_data = {
        "fatigue": data.fatigue,
        "nausea": data.nausea,
        "pain": data.pain,
        "appetite": data.appetite,
        "sleep_hours": data.sleep_hours
    }
    
    user_id = uuid.UUID(current_user["sub"])
    new_log = SymptomLog(
        user_id=user_id,
        symptoms=symptoms_data,
        mood=str(data.mood),
        notes=data.journal_text,
        logged_at=_parse_logged_at(data.date)
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    alert = None
    if data.pain >= 8 or data.nausea >= 8:
        alert = "Your symptoms look severe today. Please contact your care team if this persists."

    return {"status": "success", "id": new_log.id, "alert": alert}

@router.get("/trends")
async def get_trends(days: int = 14, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch recent symptom logs to visualize trends."""
    user_id = uuid.UUID(current_user["sub"])
    logs = db.query(SymptomLog).filter(SymptomLog.user_id == user_id).order_by(desc(SymptomLog.logged_at)).limit(days).all()
    
    # Flatten JSON symptoms for the frontend chart
    flattened_trends = []
    for log in reversed(logs):
        symptoms = _coerce_symptoms(getattr(log, "symptoms", None))
        item = {
            "id": log.id,
            "logged_at": log.logged_at,
            "mood": _coerce_mood(getattr(log, "mood", None)),
            "notes": log.notes,
            "fatigue": symptoms.get("fatigue", 0),
            "nausea": symptoms.get("nausea", 0),
            "pain": symptoms.get("pain", 0),
            "appetite": symptoms.get("appetite", 0),
            "sleep_hours": symptoms.get("sleep_hours", 0),
        }

        # Preserve any additional keys that may exist in older/newer payloads.
        item.update(symptoms)
        flattened_trends.append(item)
        
    return {"trends": flattened_trends}
