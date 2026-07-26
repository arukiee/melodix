"""Standardized AI response envelope."""

from pydantic import BaseModel

class AIResponse(BaseModel):
    content: str
    usage: dict | None = None
    errors: list[str] | None = None
