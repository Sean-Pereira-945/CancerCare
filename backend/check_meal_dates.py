from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    res = conn.execute(text('SELECT date, adhered_to_plan FROM meal_logs ORDER BY date DESC LIMIT 5'))
    rows = res.fetchall()
    print(f"Latest logs ({len(rows)}):")
    for r in rows:
        print(f"Date: {r[0]}, Adhered: {r[1]}")
