"""Notification configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings

class NotificationSettings(BaseSettings):
    email_sender: str | None = None
    email_smtp_url: str | None = None
    push_service_url: str | None = None

    class Config:
        env_prefix = ""
