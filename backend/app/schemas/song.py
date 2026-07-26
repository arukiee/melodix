# backend/app/schemas/song.py
"""Pydantic schemas for the core Song entity.
These schemas map directly to the `Song` SQLAlchemy model and its related
objects via `from_attributes=True` for seamless ORM serialization.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

# Base class with common config
class SongBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    subtitle: Optional[str] = None
    arranger: Optional[str] = None
    copyright: Optional[str] = None
    difficulty_override: Optional[int] = None
    thumbnail_uri: Optional[str] = None
    preview_audio_uri: Optional[str] = None
    lyrics_available: Optional[bool] = None
    is_public: Optional[bool] = None
    created_by: Optional[int] = None
    instrument_id: Optional[int] = None
    genre_id: Optional[int] = None
    language_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

class SongCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str
    subtitle: Optional[str] = None
    arranger: Optional[str] = None
    copyright: Optional[str] = None
    instrument_id: Optional[int] = None
    genre_id: Optional[int] = None
    language_id: Optional[int] = None
    difficulty_override: Optional[int] = None
    thumbnail_uri: Optional[str] = None
    preview_audio_uri: Optional[str] = None
    lyrics_available: Optional[bool] = None
    is_public: Optional[bool] = False
    created_by: Optional[int] = None
    published_at: Optional[datetime] = None

class SongUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: Optional[str] = None
    subtitle: Optional[str] = None
    arranger: Optional[str] = None
    copyright: Optional[str] = None
    instrument_id: Optional[int] = None
    genre_id: Optional[int] = None
    language_id: Optional[int] = None
    difficulty_override: Optional[int] = None
    thumbnail_uri: Optional[str] = None
    preview_audio_uri: Optional[str] = None
    lyrics_available: Optional[bool] = None
    is_public: Optional[bool] = None
    published_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

class SongSummary(SongBase):
    """Lightweight representation used in list views."""
    pass

class SongDetail(SongBase):
    """Full representation including related collections.
    The nested collections are defined in their own schema modules and
    imported here to avoid circular imports.
    """
    files: List["SongFileDetail"] = []
    difficulty: Optional["SongDifficultyDetail"] = None
    techniques: List["SongTechniqueDetail"] = []
    skills: List["SkillDetail"] = []
    events: List["SongEventDetail"] = []
    ground_truth_meta: Optional["SongGroundTruthMetaDetail"] = None
    analytics: Optional["SongAnalyticsDetail"] = None

# Forward references for type checking
from .song_file import SongFileDetail
from .song_difficulty import SongDifficultyDetail
from .song_technique import SongTechniqueDetail
from .song_skill import SkillDetail
from .song_event import SongEventDetail
from .song_ground_truth import SongGroundTruthMetaDetail
from .song_analytics import SongAnalyticsDetail
