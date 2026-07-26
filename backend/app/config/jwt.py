"""JWT configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings

class JWTSettings(BaseSettings):
    secret_key: str = Field("change_me", env="JWT_SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expires_minutes: int = 30
    refresh_token_expires_days: int = 7

    class Config:
        env_prefix = ""
