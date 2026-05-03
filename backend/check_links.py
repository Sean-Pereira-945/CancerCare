from app.database import SessionLocal
from app.models.db import User, CaregiverPatient
import uuid

def check_links():
    db = SessionLocal()
    try:
        links = db.query(CaregiverPatient).all()
        print(f"Total links found: {len(links)}")
        for l in links:
            cg = db.query(User).filter(User.id == l.caregiver_id).first()
            pt = db.query(User).filter(User.id == l.patient_id).first()
            print(f"Caregiver: {cg.email if cg else 'Unknown'} -> Patient: {pt.email if pt else 'Unknown'}")
    finally:
        db.close()

if __name__ == "__main__":
    check_links()
