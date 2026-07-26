"""Memory slice model used by orchestrator."""

from pydantic import BaseModel

class MemorySlice(BaseModel):
    user_id: str
    data: dict
