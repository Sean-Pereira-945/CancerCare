from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.auth.router import get_current_user
from app.database import get_db
from app.models.db import User, CaregiverPatient, Medication, MedicationLog, MealLog, DietPlan
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, date

router = APIRouter()

class LinkPatientRequest(BaseModel):
    email: str

class LogMealRequest(BaseModel):
    date: str
    meal_type: str
    adhered_to_plan: bool

class LogMedicationRequest(BaseModel):
    medication_id: str

@router.post("/link")
async def link_patient(data: LinkPatientRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Link a caregiver to a patient via email."""
    if current_user.get("role") != "caregiver":
        raise HTTPException(status_code=403, detail="Only caregivers can link to patients")

    # Find patient
    patient = db.query(User).filter(and_(User.email == data.email, User.role == "patient")).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Check if already linked
    existing = db.query(CaregiverPatient).filter(and_(
        CaregiverPatient.caregiver_id == current_user["sub"],
        CaregiverPatient.patient_id == patient.id
    )).first()
    
    if existing:
        return {"status": "Already linked", "patient_name": patient.name}

    # Create link
    new_link = CaregiverPatient(
        caregiver_id=current_user["sub"],
        patient_id=patient.id
    )
    db.add(new_link)
    db.commit()

    return {"status": "Linked successfully", "patient_name": patient.name}

@router.get("/patient-summary")
async def get_patient_summary(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get health overview for the patient linked to this caregiver."""
    if current_user.get("role") != "caregiver":
        raise HTTPException(status_code=403, detail="Access denied")

    # Get link
    link = db.query(CaregiverPatient).filter(CaregiverPatient.caregiver_id == current_user["sub"]).first()
    if not link:
        return {"data": None, "message": "No patient linked"}

    patient = db.query(User).filter(User.id == link.patient_id).first()
    
    # Get medications
    meds = db.query(Medication).filter(Medication.user_id == patient.id).all()
    
    # Check today's logs for each medication
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    meds_data = []
    for m in meds:
        taken_today = db.query(MedicationLog).filter(and_(
            MedicationLog.medication_id == m.id,
            MedicationLog.taken_at >= today_start
        )).first() is not None
        
        meds_data.append({
            "id": m.id,
            "name": m.name,
            "dosage": m.dosage,
            "frequency": m.frequency,
            "times": m.times,
            "notes": m.notes,
            "active": m.active,
            "taken_today": taken_today
        })

    # Get diet adherence
    meal_logs = db.query(MealLog).filter(MealLog.user_id == patient.id).all()
    total_meals = len(meal_logs)
    adhered_meals = len([m for m in meal_logs if m.adhered_to_plan])

    # Get latest diet plan
    latest_plan = db.query(DietPlan).filter(DietPlan.user_id == patient.id).order_by(DietPlan.created_at.desc()).first()
    diet_instructions = latest_plan.plan_data.get("guidelines") if latest_plan and latest_plan.plan_data else None

    return {
        "data": {
            "patient": {
                "name": patient.name,
                "email": patient.email,
                "cancer_type": patient.cancer_type
            },
            "medications": meds_data,
            "diet_instructions": diet_instructions,
            "diet_adherence": {
                "total": total_meals,
                "adhered": adhered_meals,
                "percentage": round(adhered_meals / total_meals * 100 if total_meals > 0 else 0, 1)
            }
        }
    }

@router.post("/log-meal")
async def log_patient_meal(data: LogMealRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Caregiver logs a meal for the patient."""
    link = db.query(CaregiverPatient).filter(CaregiverPatient.caregiver_id == current_user["sub"]).first()
    if not link:
        raise HTTPException(status_code=404, detail="No linked patient found")

    new_log = MealLog(
        user_id=link.patient_id,
        date=datetime.fromisoformat(data.date.replace('Z', '')),
        meal_type=data.meal_type,
        adhered_to_plan=data.adhered_to_plan
    )
    db.add(new_log)
    db.commit()
    return {"status": "Meal logged"}

@router.post("/log-medication")
async def log_patient_medication(data: LogMedicationRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Caregiver marks a patient's medication as taken."""
    link = db.query(CaregiverPatient).filter(CaregiverPatient.caregiver_id == current_user["sub"]).first()
    if not link:
        raise HTTPException(status_code=404, detail="No linked patient found")

    # Verify medication belongs to patient
    med = db.query(Medication).filter(and_(Medication.id == data.medication_id, Medication.user_id == link.patient_id)).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found for this patient")

    new_log = MedicationLog(
        user_id=link.patient_id,
        medication_id=data.medication_id,
        status="taken"
    )
    db.add(new_log)
    db.commit()
    return {"status": "Medication logged"}
