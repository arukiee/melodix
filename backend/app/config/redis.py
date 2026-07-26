"""Redis configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings

class RedisSettings(BaseSettings):
    url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    ttl_seconds: int = 300

    class Config:
        env_prefix = ""
