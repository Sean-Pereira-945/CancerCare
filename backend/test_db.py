from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("NEON_POSTGRES_URL")
print(f"Testing connection to: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"Connection successful: {result.fetchone()}")
except Exception as e:
    print(f"Connection failed: {e}")
