from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient
from functools import lru_cache
from app.config import get_settings
import os

settings = get_settings()

# --- SQLAlchemy Setup (SQL) ---
DATABASE_URL = settings.neon_database_url or settings.neon_postgres_url

# Fallback to local sqlite if no DB URL is provided
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./cancercare.db"

engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    # Needed for SQLite
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- MongoDB Setup (Documents) ---
@lru_cache(maxsize=1)
def get_mongo():
    """Get MongoDB database instance with a basic in-memory fallback for testing/dev."""
    if not settings.mongodb_uri:
        # Simple dummy for local dev if Mongo isn't configured
        class DummyMongo:
            def __getitem__(self, name):
                return self
            def find(self, *args, **kwargs): return []
            def find_one(self, *args, **kwargs): return None
            def insert_one(self, *args, **kwargs): pass
            def update_one(self, *args, **kwargs): pass
            def delete_many(self, *args, **kwargs): pass
            def sort(self, *args, **kwargs): return self
        return DummyMongo()

    try:
        client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        return client["cancercare"]
    except Exception:
        # Fallback to dummy
        return get_mongo.__wrapped__(None)

