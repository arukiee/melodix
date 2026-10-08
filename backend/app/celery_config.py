from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from datetime import timedelta

class CelerySettings(BaseSettings):
    broker_url: str = Field(default="redis://redis:6379/0", validation_alias="CELERY_BROKER_URL")
    result_backend: str = Field(default="redis://redis:6379/1", validation_alias="CELERY_RESULT_BACKEND")
    task_default_retry_delay: int = Field(default=5, validation_alias="CELERY_RETRY_DELAY")
    task_max_retries: int = Field(default=3, validation_alias="CELERY_MAX_RETRIES")
    beat_schedule: dict = {
        "cleanup-temp-every-hour": {
            "task": "maintenance.cleanup_temp_files",
            "schedule": timedelta(hours=1),
        },
    }
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )
