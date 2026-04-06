from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.auth.router import get_current_user
from app.ml.sentiment import analyze_mood
from app.database import get_mongo
from datetime import datetime, timedelta

router = APIRouter()


class SymptomLog(BaseModel):
    date: str
    fatigue: int        # 1-10
    nausea: int         # 1-10
    pain: int           # 1-10
    appetite: int       # 1-10
    mood: int           # 1-10
    sleep_hours: float
    journal_text: Optional[str] = ""


@router.post("/log")
async def log_symptoms(log: SymptomLog, current_user: dict = Depends(get_current_user)):
    """Log daily symptoms with optional mood journal analysis."""
    mongo = get_mongo()
    user_id = current_user["sub"]

    # Analyze journal mood using sentiment model
    sentiment = analyze_mood(log.journal_text) if log.journal_text else {}

    # Check for consistently low mood (alert after 3 days of low mood)
    three_days_ago = datetime.utcnow() - timedelta(days=3)
    recent = list(mongo["symptoms"].find({
        "user_id": user_id,
        "logged_at": {"$gte": three_days_ago}
    }))
    low_mood_alert = (
        len(recent) >= 2
        and all(r.get("mood", 5) <= 3 for r in recent)
        and log.mood <= 3
    )

    mongo["symptoms"].insert_one({
        "user_id": user_id,
        **log.dict(),
        "sentiment": sentiment,
        "logged_at": datetime.utcnow()
    })

    response = {"status": "Symptom log saved"}
    if low_mood_alert:
        response["alert"] = (
            "We noticed you have been feeling low for a few days. "
            "Please consider speaking with your care team or a counselor. "
            "You are not alone. 💙"
        )
    return response


@router.get("/trends")
async def get_trends(days: int = 14, current_user: dict = Depends(get_current_user)):
    """Get symptom trends over the past N days for charting."""
    mongo = get_mongo()
    since = datetime.utcnow() - timedelta(days=days)
    logs = list(mongo["symptoms"].find(
        {"user_id": current_user["sub"], "logged_at": {"$gte": since}},
        {"_id": 0}
    ).sort("logged_at", 1))

    # Convert datetime objects to strings for JSON serialization
    for log in logs:
        if "logged_at" in log and hasattr(log["logged_at"], "isoformat"):
            log["logged_at"] = log["logged_at"].isoformat()

    return {"trends": logs, "days": days}
