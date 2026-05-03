from app.database import engine
from sqlalchemy import text
import json

with engine.connect() as conn:
    res = conn.execute(text('SELECT filename, extracted_fields FROM reports ORDER BY uploaded_at DESC LIMIT 1'))
    row = res.fetchone()
    if row:
        print(f"File: {row[0]}")
        print(f"Extracted: {json.dumps(row[1], indent=2)}")
    else:
        print("No reports found")
