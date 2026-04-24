from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.auth.router import get_current_user
from app.database import get_db
from app.models.db import Medication
from sqlalchemy.orm import Session
from sqlalchemy import and_

router = APIRouter()

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
    new_med = Medication(
        user_id=current_user["sub"],
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
    """Get all active medications for the current user."""
    meds = db.query(Medication).filter(Medication.user_id == current_user["sub"]).all()
    return {"medications": meds}

@router.put("/{medication_id}")
async def update_medication_status(
    medication_id: str,
    update: MedicationUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update medication status (active/inactive)."""
    med = db.query(Medication).filter(and_(Medication.id == medication_id, Medication.user_id == current_user["sub"])).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    med.active = update.active
    db.commit()
    return {"status": "Updated", "medication": med}

@router.delete("/{med_id}")
async def delete_medication(med_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a medication."""
    med = db.query(Medication).filter(and_(Medication.id == med_id, Medication.user_id == current_user["sub"])).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    db.delete(med)
    db.commit()
    return {"status": "deleted"}
