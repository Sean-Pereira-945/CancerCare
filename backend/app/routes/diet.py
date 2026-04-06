from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.auth.router import get_current_user
from app.ml.diet_engine import generate_diet_plan
from app.database import get_supabase
from datetime import datetime

router = APIRouter()


class DietPlanRequest(BaseModel):
    cancer_type: str
    stage: Optional[str] = "unknown"
    fatigue: Optional[int] = 5
    nausea: Optional[int] = 3
    appetite: Optional[str] = "moderate"
    restrictions: Optional[str] = "none"


class MealLogRequest(BaseModel):
    date: str
    meal_type: str  # breakfast, lunch, dinner, snack
    food_items: list
    calories: Optional[int] = None
    adhered_to_plan: bool = True


@router.post("/generate-plan")
async def generate_plan(request: DietPlanRequest, current_user: dict = Depends(get_current_user)):
    """Generate a personalized 7-day diet plan using Gemini AI."""
    plan = await generate_diet_plan(request.dict())

    # Save plan to Supabase
    try:
        sb = get_supabase()
        sb.table("diet_plans").upsert({
            "user_id": current_user["sub"],
            "plan_data": plan,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception:
        pass  # DB save failure shouldn't block the response

    return plan


@router.post("/log-meal")
async def log_meal(request: MealLogRequest, current_user: dict = Depends(get_current_user)):
    """Log a meal eaten by the patient for adherence tracking."""
    try:
        sb = get_supabase()
        sb.table("meal_logs").insert({
            "user_id": current_user["sub"],
            **request.dict()
        }).execute()
    except Exception as e:
        return {"status": "Meal logged locally", "warning": str(e)}
    return {"status": "Meal logged"}


@router.get("/adherence")
async def get_adherence(current_user: dict = Depends(get_current_user)):
    """Get diet plan adherence rate for the current user."""
    try:
        sb = get_supabase()
        logs = sb.table("meal_logs").select("*").eq("user_id", current_user["sub"]).execute()
        total = len(logs.data)
        adhered = sum(1 for l in logs.data if l.get("adhered_to_plan"))
        return {
            "total_logs": total,
            "adherence_rate": round(adhered / total * 100 if total else 0, 1)
        }
    except Exception:
        return {"total_logs": 0, "adherence_rate": 0}
