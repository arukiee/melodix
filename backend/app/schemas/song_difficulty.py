# backend/app/schemas/song_difficulty.py
"""Pydantic schemas for SongDifficulty.
Mapped to the `SongDifficulty` SQLAlchemy model.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

class SongDifficultyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, orm_mode=True)
    id: int
    song_id: int
    difficulty_level: int
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class SongDifficultyCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, orm_mode=True)
    song_id: int
    difficulty_level: int
    notes: Optional[str] = None

class SongDifficultyUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, orm_mode=True)
    difficulty_level: Optional[int] = None
    notes: Optional[str] = None

class SongDifficultyDetail(SongDifficultyBase):
    """Full representation of a song's difficulty metadata."""
    pass
