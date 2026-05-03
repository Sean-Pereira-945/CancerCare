from app.database import SessionLocal
from app.models.db import User, CaregiverPatient, Medication
import uuid

def simulate_summary(caregiver_email):
    db = SessionLocal()
    try:
        cg = db.query(User).filter(User.email == caregiver_email).first()
        if not cg:
            print(f"Caregiver {caregiver_email} not found")
            return
        
        link = db.query(CaregiverPatient).filter(CaregiverPatient.caregiver_id == cg.id).first()
        if not link:
            print("No link found")
            return
            
        patient = db.query(User).filter(User.id == link.patient_id).first()
        print(f"Patient: {patient.email}")
        
        meds = db.query(Medication).filter(Medication.user_id == patient.id).all()
        print(f"Found {len(meds)} meds for patient")
        for m in meds:
            print(f"- {m.name}")
    finally:
        db.close()

if __name__ == "__main__":
    simulate_summary("jhonnyboy@gmail.com")
