# Database Migration Notes

This project currently uses SQLAlchemy models in `backend/app/models/db.py`.

## Why this exists
- Prevent unmanaged schema drift in shared Postgres environments.
- Track schema fixes explicitly (especially UUID/varchar mismatches).

## Immediate schema mismatch to fix
If your existing Postgres `users.id` is `uuid` while model FKs are `varchar(36)`, DDL can fail for:
- `medication_logs.user_id -> users.id`
- similar FK pairs in other tables

## Suggested migration strategy
1. Back up database.
2. Choose one canonical type for all primary and foreign key IDs (`uuid` recommended in Postgres).
3. Convert FK columns to match `users.id` type.
4. Recreate FK constraints.

## Example SQL approach (adapt to your schema)
```sql
ALTER TABLE medication_logs
  ALTER COLUMN user_id TYPE uuid USING user_id::uuid;

ALTER TABLE medications
  ALTER COLUMN user_id TYPE uuid USING user_id::uuid;
```

Then recreate constraints if needed:
```sql
ALTER TABLE medication_logs
  DROP CONSTRAINT IF EXISTS medication_logs_user_id_fkey,
  ADD CONSTRAINT medication_logs_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES users(id);
```

## Longer-term
- Adopt Alembic for versioned migrations (`alembic init`, revision files, upgrade flow).
- Run migrations in CI before app startup.

## Migration script added in this repo
For immediate UUID alignment in existing Postgres environments, run:

```bash
cd backend
set PYTHONPATH=.
python migrations/001_uuid_fk_alignment.py
```

PowerShell variant:

```powershell
Set-Location backend
$env:PYTHONPATH='.'
python migrations/001_uuid_fk_alignment.py
```
