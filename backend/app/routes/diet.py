from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Union
from app.auth.router import get_current_user
from app.ml.diet_engine import generate_diet_plan
from datetime import datetime
from app.database import get_db
from app.models.db import DietPlan, MealLog
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, Integer
import uuid

router = APIRouter()

class DietPlanRequest(BaseModel):
    cancer_type: str
    stage: Optional[str] = "unspecified"
    fatigue: int = Field(default=5, ge=1, le=10)
    nausea: int = Field(default=3, ge=1, le=10)
    appetite: Optional[str] = "moderate"
    restrictions: Optional[Union[str, List[str]]] = "none"
    symptoms: List[str] = Field(default_factory=list)
    preferences: Optional[Union[str, List[str]]] = None

class MealLogRequest(BaseModel):
    date: str
    meal_type: str
    adhered_to_plan: bool


def _as_clean_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part and part.strip()]
    if isinstance(value, list):
        return [str(part).strip() for part in value if str(part).strip()]
    return [str(value).strip()] if str(value).strip() else []

@router.post("/generate-plan")
async def generate_plan(request: DietPlanRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate a personalized 7-day diet plan using Gemini AI."""
    payload = request.model_dump()
    restrictions_list = _as_clean_list(payload.get("restrictions"))
    preferences_list = _as_clean_list(payload.get("preferences"))
    symptoms_list = _as_clean_list(payload.get("symptoms"))

    payload["restrictions_list"] = restrictions_list
    payload["restrictions"] = ", ".join(restrictions_list) if restrictions_list else "none"
    payload["preferences_list"] = preferences_list
    payload["preferences"] = ", ".join(preferences_list) if preferences_list else "none"
    payload["symptoms"] = symptoms_list

    try:
        plan = await generate_diet_plan(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate diet plan: {str(e)}")

    # Save plan to database
    try:
        user_id = uuid.UUID(current_user["sub"])
        new_plan = DietPlan(
            user_id=user_id,
            plan_data=plan
        )
        db.add(new_plan)
        db.commit()
    except Exception:
        pass  # DB save failure shouldn't block the response

    return plan

@router.post("/log-meal")
async def log_meal(request: MealLogRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Log a patient's meal for diet adherence tracking."""
    try:
        user_id = uuid.UUID(current_user["sub"])
        new_log = MealLog(
            user_id=user_id,
            date=datetime.fromisoformat(request.date.replace('Z', '')),
            meal_type=request.meal_type,
            adhered_to_plan=request.adhered_to_plan
        )
        db.add(new_log)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log meal: {str(e)}")
    return {"status": "Meal logged"}
@router.get("/adherence-trends")
async def get_adherence_trends(days: int = 7, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get daily diet adherence percentage for the last X days."""
    from sqlalchemy import func
    user_id = uuid.UUID(current_user["sub"])
    
    # Query daily adherence
    logs = db.query(
        func.date(MealLog.date).label('day'),
        func.count(MealLog.id).label('total'),
        func.sum(func.cast(MealLog.adhered_to_plan, Integer)).label('adhered')
    ).filter(MealLog.user_id == user_id).group_by(func.date(MealLog.date)).order_by(func.date(MealLog.date)).limit(days).all()
    
    trends = []
    for log in logs:
        trends.append({
            "date": log.day.isoformat() if hasattr(log.day, 'isoformat') else str(log.day),
            "rate": round((log.adhered / log.total) * 100, 1) if log.total > 0 else 0
        })
    return trends
