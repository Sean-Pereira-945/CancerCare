from __future__ import annotations

from sqlalchemy import text

from app.database import engine


FK_COLUMNS = [
    ("diet_plans", "id"),
    ("diet_plans", "user_id"),
    ("meal_logs", "id"),
    ("meal_logs", "user_id"),
    ("medications", "id"),
    ("medications", "user_id"),
    ("medication_logs", "id"),
    ("medication_logs", "user_id"),
    ("medication_logs", "medication_id"),
    ("symptom_logs", "id"),
    ("symptom_logs", "user_id"),
    ("caregiver_patients", "id"),
    ("caregiver_patients", "caregiver_id"),
    ("caregiver_patients", "patient_id"),
]


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    query = text(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = :table_name
          AND column_name = :column_name
        LIMIT 1
        """
    )
    return conn.execute(query, {"table_name": table_name, "column_name": column_name}).scalar() is not None


def _column_is_uuid(conn, table_name: str, column_name: str) -> bool:
    query = text(
        """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = :table_name
          AND column_name = :column_name
        """
    )
    data_type = conn.execute(query, {"table_name": table_name, "column_name": column_name}).scalar()
    return data_type == "uuid"


def _drop_fk_constraints(conn, table_name: str) -> None:
    query = text(
        """
        SELECT tc.constraint_name
        FROM information_schema.table_constraints tc
        WHERE tc.table_schema = 'public'
          AND tc.table_name = :table_name
          AND tc.constraint_type = 'FOREIGN KEY'
        """
    )
    for row in conn.execute(query, {"table_name": table_name}):
        conn.execute(text(f'ALTER TABLE "{table_name}" DROP CONSTRAINT IF EXISTS "{row.constraint_name}"'))


def _recreate_known_constraints(conn) -> None:
    statements = [
        "ALTER TABLE medication_logs ADD CONSTRAINT medication_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)",
        "ALTER TABLE medication_logs ADD CONSTRAINT medication_logs_medication_id_fkey FOREIGN KEY (medication_id) REFERENCES medications(id)",
        "ALTER TABLE medications ADD CONSTRAINT medications_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)",
        "ALTER TABLE diet_plans ADD CONSTRAINT diet_plans_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)",
        "ALTER TABLE meal_logs ADD CONSTRAINT meal_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)",
        "ALTER TABLE symptom_logs ADD CONSTRAINT symptom_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)",
        "ALTER TABLE caregiver_patients ADD CONSTRAINT caregiver_patients_caregiver_id_fkey FOREIGN KEY (caregiver_id) REFERENCES users(id)",
        "ALTER TABLE caregiver_patients ADD CONSTRAINT caregiver_patients_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES users(id)",
    ]

    for statement in statements:
        try:
            conn.execute(text(statement))
        except Exception:
            # Constraint may already exist; keep migration idempotent.
            pass


def run_migration() -> None:
    if engine.dialect.name != "postgresql":
        print(f"Skipping migration: dialect '{engine.dialect.name}' does not require UUID alignment.")
        return

    with engine.begin() as conn:
        for table_name in {
            "diet_plans",
            "meal_logs",
            "medications",
            "medication_logs",
            "symptom_logs",
            "caregiver_patients",
        }:
            if _column_exists(conn, table_name, "id"):
                _drop_fk_constraints(conn, table_name)

        for table_name, column_name in FK_COLUMNS:
            if not _column_exists(conn, table_name, column_name):
                continue
            if _column_is_uuid(conn, table_name, column_name):
                continue

            print(f"Altering {table_name}.{column_name} to UUID...")
            conn.execute(
                text(
                    f'ALTER TABLE "{table_name}" '
                    f'ALTER COLUMN "{column_name}" TYPE uuid '
                    f'USING NULLIF("{column_name}"::text, \'\')::uuid'
                )
            )

        _recreate_known_constraints(conn)

    print("Migration complete: UUID PK/FK alignment applied.")


if __name__ == "__main__":
    run_migration()
