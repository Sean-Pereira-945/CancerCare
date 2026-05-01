from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.auth.router import get_current_user
from app.database import get_db
from app.models.db import User, CaregiverPatient, Medication, MedicationLog, MealLog, DietPlan, SymptomLog, Report
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, date, timezone
import uuid

router = APIRouter()

class LinkPatientRequest(BaseModel):
    patient_email: str

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

    # Find user by email first
    email_clean = data.patient_email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()
    
    if not user:
        raise HTTPException(status_code=404, detail=f"No user found with email: {email_clean}")
    
    if user.role != "patient":
        raise HTTPException(status_code=400, detail=f"User {email_clean} is registered as a {user.role}, not a patient.")

    user_id = uuid.UUID(current_user["sub"])
    # Check if already linked
    existing = db.query(CaregiverPatient).filter(and_(
        CaregiverPatient.caregiver_id == user_id,
        CaregiverPatient.patient_id == user.id
    )).first()
    
    if existing:
        # Update timestamp to make it the 'latest' link
        existing.linked_at = datetime.now(timezone.utc)
        db.commit()
        return {"status": "Already linked", "patient_name": user.name}

    # Create link
    try:
        new_link = CaregiverPatient(
            caregiver_id=user_id,
            patient_id=user.id,
            linked_at=datetime.now(timezone.utc)
        )
        db.add(new_link)
        db.commit()
        return {"status": "Linked successfully", "patient_name": user.name}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Linking failed: {str(e)}")

@router.get("/patient-summary")
async def get_patient_summary(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get health overview for the patient linked to this caregiver."""
    if current_user.get("role") != "caregiver":
        raise HTTPException(status_code=403, detail="Access denied")

    user_id = uuid.UUID(current_user["sub"])
    # Get the most recently linked patient
    link = db.query(CaregiverPatient).filter(CaregiverPatient.caregiver_id == user_id).order_by(desc(CaregiverPatient.linked_at)).first()
    if not link:
        return {}

    patient = db.query(User).filter(User.id == link.patient_id).first()
    
    # Get medications
    meds = db.query(Medication).filter(Medication.user_id == patient.id).all()
    
    # Check today's logs for each medication
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
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
    diet_info = {
        "guidelines": latest_plan.plan_data.get("guidelines"),
        "full_plan": latest_plan.plan_data.get("plan")
    } if latest_plan and latest_plan.plan_data else None

    # Get symptom trends (last 7 days)
    symptom_logs = db.query(SymptomLog).filter(SymptomLog.user_id == patient.id).order_by(desc(SymptomLog.logged_at)).limit(7).all()
    symptoms_summary = []
    for log in symptom_logs:
        symptoms_summary.append({
            "date": log.logged_at,
            "mood": log.mood,
            "pain": log.symptoms.get("pain", 0) if isinstance(log.symptoms, dict) else 0,
            "fatigue": log.symptoms.get("fatigue", 0) if isinstance(log.symptoms, dict) else 0
        })

    # Get reports
    reports = db.query(Report).filter(Report.user_id == patient.id).order_by(desc(Report.uploaded_at)).all()
    reports_data = [{
        "filename": r.filename,
        "uploaded_at": r.uploaded_at,
        "extracted_fields": r.extracted_fields
    } for r in reports]

    return {
        "patient": {
            "name": patient.name,
            "email": patient.email,
            "cancer_type": patient.cancer_type
        },
        "medications": meds_data,
        "diet_instructions": diet_info,
        "symptom_trends": symptoms_summary,
        "reports": reports_data,
        "diet_adherence": {
            "total": total_meals,
            "adhered": adhered_meals,
            "rate": round(adhered_meals / total_meals * 100 if total_meals > 0 else 0, 1)
        }
    }

@router.post("/log-meal")
async def log_patient_meal(data: LogMealRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Caregiver logs a meal for the patient."""
    user_id = uuid.UUID(current_user["sub"])
    # Always use the most recent link
    link = db.query(CaregiverPatient).filter(CaregiverPatient.caregiver_id == user_id).order_by(desc(CaregiverPatient.linked_at)).first()
    if not link:
        raise HTTPException(status_code=404, detail="No linked patient found. Please link to a patient first.")

    try:
        # Better date parsing
        print(f"DEBUG: Incoming meal date: {data.date}")
        clean_date = data.date.replace('Z', '').split('.')[0] # Remove milliseconds and Z
        new_log = MealLog(
            user_id=link.patient_id,
            date=datetime.fromisoformat(clean_date),
            meal_type=data.meal_type,
            adhered_to_plan=data.adhered_to_plan
        )
        db.add(new_log)
        db.commit()
        return {"status": "Meal logged"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/log-medication")
async def log_patient_medication(data: LogMedicationRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Caregiver marks a patient's medication as taken."""
    user_id = uuid.UUID(current_user["sub"])
    link = db.query(CaregiverPatient).filter(CaregiverPatient.caregiver_id == user_id).order_by(desc(CaregiverPatient.linked_at)).first()
    if not link:
        raise HTTPException(status_code=404, detail="No linked patient found")

    # Verify medication belongs to patient
    med = db.query(Medication).filter(and_(Medication.id == data.medication_id, Medication.user_id == link.patient_id)).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found for this patient")

    try:
        new_log = MedicationLog(
            user_id=link.patient_id,
            medication_id=data.medication_id,
            status="taken",
            taken_at=datetime.now(timezone.utc)
        )
        db.add(new_log)
        db.commit()
        return {"status": "Medication logged"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
