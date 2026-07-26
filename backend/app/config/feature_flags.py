"""Feature flag settings."""

from pydantic_settings import BaseSettings

class FeatureFlagSettings(BaseSettings):
    ENABLE_AI_CHAT: bool = False
    ENABLE_RAG: bool = False
    ENABLE_AUDIO_ANALYSIS: bool = False
    ENABLE_NOTIFICATIONS: bool = True
    ENABLE_EMAIL: bool = False
    ENABLE_WEBSOCKETS: bool = True

    class Config:
        env_prefix = ""
