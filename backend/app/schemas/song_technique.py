# backend/app/schemas/song_technique.py
"""Pydantic schemas for SongTechnique (junction table between Song and Technique)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

class SongTechniqueBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, orm_mode=True)
    id: int
    song_id: int
    technique_id: int
    created_at: datetime
    updated_at: datetime

class SongTechniqueCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, orm_mode=True)
    song_id: int
    technique_id: int

class SongTechniqueUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, orm_mode=True)
    technique_id: Optional[int] = None

class SongTechniqueDetail(SongTechniqueBase):
    """Full representation; can include nested TechniqueDetail via imports in SongDetail."""
    pass
