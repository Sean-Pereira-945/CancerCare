from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # LLM APIs
    gemini_api_key: str = ""
    groq_api_key: str = ""
    huggingface_api_key: str = ""

    # Databases
    neon_database_url: str = ""
    neon_postgres_url: str = ""
    mongodb_uri: str = ""
    upstash_redis_url: str = ""
    mongodb_strict: bool = False

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
    auto_create_tables: bool = True

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings():
    return Settings()
