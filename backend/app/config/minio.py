"""MinIO configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class MinIOSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    endpoint: str = Field(default="http://minio:9000", validation_alias="MINIO_ENDPOINT")
    access_key: str = Field(default="melodix", validation_alias="MINIO_ROOT_USER")
    secret_key: str = Field(default="melodix_dev_password", validation_alias="MINIO_ROOT_PASSWORD")
    secure: bool = Field(default=False, validation_alias="MINIO_SECURE")
    bucket_name: str = Field(default="melodix", validation_alias="MINIO_BUCKET")
