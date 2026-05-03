import sys
from app.database import SessionLocal
from app.models.db import User
from app.auth.utils import hash_password
import uuid

def reset_password(email, new_password):
    db = SessionLocal()
    email_clean = email.lower().strip()
    try:
        user = db.query(User).filter(User.email == email_clean).first()
        if not user:
            print(f"Error: User with email '{email}' not found.")
            return
        
        user.password_hash = hash_password(new_password)
        db.commit()
        print(f"Success: Password for {email} has been reset to '{new_password}'.")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python reset_password.py <email> <new_password>")
    else:
        reset_password(sys.argv[1], sys.argv[2])
