from pydantic_settings import BaseSettings
"""Aggregate all configuration sections into a single Settings object."""

from pathlib import Path
from .database import DatabaseSettings
from .redis import RedisSettings
from .jwt import JWTSettings
from .minio import MinIOSettings
from .ollama import OllamaSettings
from .notifications import NotificationSettings
from .feature_flags import FeatureFlagSettings

class Settings(BaseSettings):
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

    DATABASE: DatabaseSettings = DatabaseSettings()
    REDIS: RedisSettings = RedisSettings()
    JWT: JWTSettings = JWTSettings()
    MINIO: MinIOSettings = MinIOSettings()
    OLLAMA: OllamaSettings = OllamaSettings()
    NOTIFICATIONS: NotificationSettings = NotificationSettings()
    FEATURE_FLAGS: FeatureFlagSettings = FeatureFlagSettings()

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
