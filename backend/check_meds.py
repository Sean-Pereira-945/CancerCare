from app.database import SessionLocal
from app.models.db import User, Medication
import uuid

def check_meds(email):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"User {email} not found")
            return
        
        meds = db.query(Medication).filter(Medication.user_id == user.id).all()
        print(f"Found {len(meds)} medications for {email}")
        for m in meds:
            print(f"- {m.name} ({m.dosage})")
    finally:
        db.close()

if __name__ == "__main__":
    check_meds("djones@gmail.com")
