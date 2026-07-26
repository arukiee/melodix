"""MinIO configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings

class MinIOSettings(BaseSettings):
    endpoint: str = Field(..., env="MINIO_ENDPOINT")
    access_key: str = Field(..., env="MINIO_ACCESS_KEY")
    secret_key: str = Field(..., env="MINIO_SECRET_KEY")
    bucket_name: str = Field(default="melodix-media")

    class Config:
        env_prefix = ""
