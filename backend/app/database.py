from supabase import create_client
from pymongo import MongoClient
from functools import lru_cache
from app.config import get_settings

settings = get_settings()


@lru_cache(maxsize=1)
def get_supabase():
    """Get Supabase client (PostgreSQL). Uses free 500MB tier."""
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError("Supabase credentials not configured. Set SUPABASE_URL and SUPABASE_KEY in .env")
    return create_client(settings.supabase_url, settings.supabase_key)


@lru_cache(maxsize=1)
def get_mongo():
    """Get MongoDB database instance. Uses free 512MB Atlas tier."""
    if not settings.mongodb_uri:
        raise RuntimeError("MongoDB URI not configured. Set MONGODB_URI in .env")
    client = MongoClient(settings.mongodb_uri)
    return client["cancercare"]
