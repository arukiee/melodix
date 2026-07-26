"""Ollama configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings

class OllamaSettings(BaseSettings):
    host: str = Field(default="http://localhost:11434")
    model: str = Field(default="llama3")

    class Config:
        env_prefix = ""
