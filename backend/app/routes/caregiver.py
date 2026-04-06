from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.auth.router import get_current_user
from app.database import get_supabase

router = APIRouter()


class CaregiverLink(BaseModel):
    patient_email: str


@router.post("/link")
async def link_to_patient(link: CaregiverLink, current_user: dict = Depends(get_current_user)):
    """Link a caregiver account to a patient by email."""
    if current_user.get("role") != "caregiver":
        raise HTTPException(status_code=403, detail="Only caregivers can link to patients")

    try:
        sb = get_supabase()
        # Find patient by email
        patient = sb.table("users").select("id, name").eq("email", link.patient_email).execute()
        if not patient.data:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Update caregiver's caregiver_for field
        sb.table("users").update({
            "caregiver_for": patient.data[0]["id"]
        }).eq("id", current_user["sub"]).execute()

        return {"status": "Linked", "patient_name": patient.data[0]["name"]}
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/patient-summary")
async def get_patient_summary(current_user: dict = Depends(get_current_user)):
    """Get a summary of the linked patient's health data for the caregiver."""
    if current_user.get("role") != "caregiver":
        raise HTTPException(status_code=403, detail="Only caregivers can access this")

    try:
        sb = get_supabase()
        # Get caregiver's linked patient
        caregiver = sb.table("users").select("caregiver_for").eq("id", current_user["sub"]).execute()
        if not caregiver.data or not caregiver.data[0].get("caregiver_for"):
            return {"error": "No patient linked. Use /link first."}

        patient_id = caregiver.data[0]["caregiver_for"]

        # Get patient info
        patient = sb.table("users").select("name, cancer_type").eq("id", patient_id).execute()

        # Get medications
        meds = sb.table("medications").select("name, dosage, active").eq("user_id", patient_id).execute()

        # Get recent meal adherence
        meals = sb.table("meal_logs").select("adhered_to_plan").eq("user_id", patient_id).execute()
        total_meals = len(meals.data)
        adhered = sum(1 for m in meals.data if m.get("adhered_to_plan"))

        return {
            "patient": patient.data[0] if patient.data else {},
            "medications": meds.data,
            "diet_adherence": {
                "total": total_meals,
                "rate": round(adhered / total_meals * 100 if total_meals else 0, 1)
            }
        }
    except Exception as e:
        return {"error": str(e)}
