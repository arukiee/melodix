import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Melodix Backend"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str
    SECRET_KEY: str = "supersecretkey_please_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OAuth
    GOOGLE_CLIENT_ID: str = "placeholder-client-id"
    GOOGLE_CLIENT_SECRET: str = "placeholder-secret"
    
    class Config:
        env_file = ".env"

settings = Settings()
