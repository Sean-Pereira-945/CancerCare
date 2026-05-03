from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    res = conn.execute(text('SELECT email, name, role FROM users'))
    users = list(res)
    print(f"Registered users: {users}")
