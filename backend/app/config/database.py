"""Database configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings

class DatabaseSettings(BaseSettings):
    url: str = Field(..., env="DATABASE_URL")
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20

    class Config:
        env_prefix = ""
