from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.auth.router import get_current_user
from app.database import get_db
from app.models.db import Medication, MedicationLog
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timezone
import uuid

router = APIRouter()

class LogMedicationRequest(BaseModel):
    medication_id: str

class MedicationCreate(BaseModel):
    name: str
    dosage: str
    frequency: str
    times: List[str] = []
    notes: Optional[str] = None

class MedicationUpdate(BaseModel):
    active: bool

@router.post("/add")
async def add_medication(data: MedicationCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Add a new medication to the patient's list."""
    user_id = uuid.UUID(current_user["sub"])
    new_med = Medication(
        user_id=user_id,
        name=data.name,
        dosage=data.dosage,
        frequency=data.frequency,
        times=data.times,
        notes=data.notes,
        active=True
    )
    db.add(new_med)
    db.commit()
    db.refresh(new_med)
    return {"status": "success", "id": new_med.id}

@router.get("/list")
async def get_medications(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all medications for the current user with today's intake status."""
    user_id = uuid.UUID(current_user["sub"])
    meds = db.query(Medication).filter(Medication.user_id == user_id).all()
    
    # Check today's logs
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    results = []
    for m in meds:
        taken_today = db.query(MedicationLog).filter(and_(
            MedicationLog.medication_id == m.id,
            MedicationLog.taken_at >= today_start
        )).first() is not None
        
        results.append({
            "id": m.id,
            "name": m.name,
            "dosage": m.dosage,
            "frequency": m.frequency,
            "times": m.times,
            "notes": m.notes,
            "active": m.active,
            "taken_today": taken_today
        })

    return {"medications": results}

@router.put("/{medication_id}")
async def update_medication_status(
    medication_id: str,
    update: MedicationUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update medication status (active/inactive)."""
    user_id = uuid.UUID(current_user["sub"])
    med = db.query(Medication).filter(and_(Medication.id == medication_id, Medication.user_id == user_id)).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    med.active = update.active
    db.commit()
    return {"status": "Updated", "medication": med}

@router.delete("/{med_id}")
async def delete_medication(med_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a medication."""
    user_id = uuid.UUID(current_user["sub"])
    med = db.query(Medication).filter(and_(Medication.id == med_id, Medication.user_id == user_id)).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    db.delete(med)
    db.commit()
    return {"status": "deleted"}
@router.post("/log")
async def log_medication(data: LogMedicationRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mark a medication as taken by the patient."""
    user_id = uuid.UUID(current_user["sub"])
    # Verify medication belongs to user
    med = db.query(Medication).filter(and_(Medication.id == data.medication_id, Medication.user_id == user_id)).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")

    new_log = MedicationLog(
        user_id=current_user["sub"],
        medication_id=data.medication_id,
        status="taken",
        taken_at=datetime.now(timezone.utc)
    )
    db.add(new_log)
    db.commit()
    return {"status": "success", "message": "Medication logged"}
