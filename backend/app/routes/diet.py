from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.auth.router import get_current_user
from app.ml.diet_engine import generate_diet_plan
from datetime import datetime
from app.database import get_db
from app.models.db import DietPlan, MealLog
from sqlalchemy.orm import Session

router = APIRouter()

class DietPlanRequest(BaseModel):
    cancer_type: str
    symptoms: list = []
    preferences: Optional[str] = None

class MealLogRequest(BaseModel):
    date: str
    meal_type: str
    adhered_to_plan: bool

@router.post("/generate-plan")
async def generate_plan(request: DietPlanRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate a personalized 7-day diet plan using Gemini AI."""
    try:
        plan = await generate_diet_plan(request.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate diet plan: {str(e)}")

    # Save plan to database
    try:
        new_plan = DietPlan(
            user_id=current_user["sub"],
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
        new_log = MealLog(
            user_id=current_user["sub"],
            date=datetime.fromisoformat(request.date.replace('Z', '')),
            meal_type=request.meal_type,
            adhered_to_plan=request.adhered_to_plan
        )
        db.add(new_log)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log meal: {str(e)}")
    return {"status": "Meal logged"}
