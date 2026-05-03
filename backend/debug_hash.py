from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    res = conn.execute(text("SELECT email, password_hash FROM users WHERE email = 'djones@gmail.com'"))
    row = res.fetchone()
    if row:
        email, phash = row
        print(f"Email: {email}")
        print(f"Hash starts with: {phash[:10]}")
    else:
        print("User not found")
