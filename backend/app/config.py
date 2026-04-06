from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # LLM APIs
    gemini_api_key: str = ""
    groq_api_key: str = ""
    huggingface_api_key: str = ""

    # Databases
    supabase_url: str = ""
    supabase_key: str = ""
    mongodb_uri: str = ""
    upstash_redis_url: str = ""

    # Auth
    jwt_secret: str = "cancercare-dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Email
    sendgrid_api_key: str = ""
    from_email: str = "noreply@cancercare.ai"

    # App
    environment: str = "development"
    frontend_url: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings():
    return Settings()
