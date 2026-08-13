from typing import Optional, ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

import os

class Settings(BaseSettings):
    env_file: ClassVar[str] = ".env.docker" if os.getenv("ENVIRONMENT") == "container" else ".env"
    model_config = SettingsConfigDict(env_file=env_file, env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Melodix AI Piano Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Core Security
    SECRET_KEY: str = "supersecretkey_please_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days

    # Databases & Cache
    DATABASE_URL: str = "sqlite:///./test.db"
    REDIS_URL: str = "redis://redis:6379/0"

    # Storage (MinIO)
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "melodix-assets"
    MINIO_USE_SSL: bool = False

    # OAuth configuration group
    class AuthConfig(BaseSettings):
        GOOGLE_CLIENT_ID: str = "955427255350-j8d7eg83h21uf67jmrdja42bgg17jofj.apps.googleusercontent.com"
        GOOGLE_CLIENT_SECRET: str = "placeholder-secret"
        GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    auth_config: AuthConfig = AuthConfig()
    OLLAMA_HOST: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3"

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
