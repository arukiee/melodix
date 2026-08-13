from pydantic import BaseSettings, ValidationError, validator
from pydantic_settings import SettingsConfigDict

PLACEHOLDER_VALUES = {
    "your_google_client_id",
    "your_google_client_secret",
    "your_jwt_secret",
    "changeme",
    "placeholder",
}

class AuthSettings(BaseSettings):
    """Environment variables required for authentication.

    This model is loaded early in the application start‑up. Any missing variable or
    placeholder value will raise a ``ValidationError`` and stop the service.
    """

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    JWT_SECRET: str = "your_jwt_secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days default

    model_config = SettingsConfigDict(env_file=".env.docker", env_file_encoding="utf-8", extra="ignore")

    @validator("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "JWT_SECRET")
    def no_placeholder(cls, v: str, field):
        if v.strip() in PLACEHOLDER_VALUES:
            raise ValueError(f"{field.name} contains a placeholder value '{v}'. Set the real credential.")
        return v

    @validator("GOOGLE_REDIRECT_URI")
    def redirect_must_be_url(cls, v: str):
        if not v.startswith("http://") and not v.startswith("https://"):
            raise ValueError("GOOGLE_REDIRECT_URI must be a valid URL.")
        return v
