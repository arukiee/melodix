# backend/app/schemas/song_skill.py
"""Pydantic schemas for the many‑to‑many relationship between Song and Skill.
The association table `song_skill` does not have its own model class; the
schemas represent the Skill objects attached to a Song.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

# Skill schemas are defined in lookups.py; we re‑export them here for a
# convenient import path when constructing SongDetail.
from .lookups import SkillDetail, SkillSummary

class SongSkillBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, orm_mode=True)
    song_id: int
    skill_id: int
    created_at: datetime
    updated_at: datetime

class SongSkillCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, orm_mode=True)
    song_id: int
    skill_id: int

class SongSkillUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, orm_mode=True)
    skill_id: Optional[int] = None

# For response payloads we expose the full Skill detail rather than the raw
# association fields.
class SongSkillDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True, orm_mode=True)
    skill: SkillDetail

class SongSkillSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, orm_mode=True)
    skill: SkillSummary
