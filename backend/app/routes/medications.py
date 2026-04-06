from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.auth.router import get_current_user
from app.database import get_supabase

router = APIRouter()


class MedicationCreate(BaseModel):
    name: str
    dosage: str = ""
    frequency: str = ""
    times: List[str] = []
    start_date: Optional[str] = None
    notes: Optional[str] = ""


class MedicationUpdate(BaseModel):
    active: bool


@router.post("/add")
async def add_medication(med: MedicationCreate, current_user: dict = Depends(get_current_user)):
    """Add a new medication to the patient's medication list."""
    try:
        sb = get_supabase()
        result = sb.table("medications").insert({
            "user_id": current_user["sub"],
            **med.dict()
        }).execute()
        return {"status": "Medication added", "medication": result.data[0] if result.data else {}}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/list")
async def list_medications(current_user: dict = Depends(get_current_user)):
    """Get all medications for the current user."""
    try:
        sb = get_supabase()
        result = sb.table("medications").select("*").eq("user_id", current_user["sub"]).execute()
        return {"medications": result.data}
    except Exception:
        return {"medications": []}


@router.put("/{medication_id}")
async def update_medication(
    medication_id: str,
    update: MedicationUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update medication status (active/inactive)."""
    try:
        sb = get_supabase()
        result = sb.table("medications").update(
            {"active": update.active}
        ).eq("id", medication_id).eq("user_id", current_user["sub"]).execute()
        return {"status": "Updated", "medication": result.data[0] if result.data else {}}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.delete("/{medication_id}")
async def delete_medication(medication_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a medication from the patient's list."""
    try:
        sb = get_supabase()
        sb.table("medications").delete().eq("id", medication_id).eq("user_id", current_user["sub"]).execute()
        return {"status": "Medication deleted"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
