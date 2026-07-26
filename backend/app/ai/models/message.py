"""Message model used for AI communication."""

from pydantic import BaseModel

class Message(BaseModel):
    role: str  # e.g., "user", "assistant"
    content: str
