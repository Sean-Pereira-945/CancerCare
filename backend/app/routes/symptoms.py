from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from app.auth.router import get_current_user
from app.database import get_db
from app.models.db import SymptomLog
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

router = APIRouter()

class SymptomLogCreate(BaseModel):
    symptoms: Dict[str, int]
    mood: str
    notes: Optional[str] = None

@router.post("/log")
async def log_symptoms(data: SymptomLogCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Save daily symptom logs to the database."""
    new_log = SymptomLog(
        user_id=current_user["sub"],
        symptoms=data.symptoms,
        mood=data.mood,
        notes=data.notes
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return {"status": "success", "id": new_log.id}

@router.get("/trends")
async def get_trends(days: int = 14, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch recent symptom logs to visualize trends."""
    logs = db.query(SymptomLog).filter(SymptomLog.user_id == current_user["sub"]).order_by(desc(SymptomLog.logged_at)).limit(days).all()
    # Return in chronological order for the chart
    return {"trends": list(reversed(logs))}
