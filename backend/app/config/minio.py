"""MinIO configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings

class MinIOSettings(BaseSettings):
    endpoint: str = Field(default="http://minio:9000", env="MINIO_ENDPOINT")
    access_key: str = Field(default="melodix", env="MINIO_ROOT_USER")
    secret_key: str = Field(default="melodix_dev_password", env="MINIO_ROOT_PASSWORD")
    secure: bool = Field(default=False, env="MINIO_SECURE")
    bucket_name: str = Field(default="melodix", env="MINIO_BUCKET")

    class Config:
        env_prefix = ""
