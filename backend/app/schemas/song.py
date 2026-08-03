from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID

class SongSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    composer: Optional[str] = None
    artist: Optional[str] = None
    genre: Optional[str] = None
    difficulty: Optional[str] = "Beginner"
    bpm: Optional[int] = 120
    key_signature: Optional[str] = "C Major"
    time_signature: Optional[str] = "4/4"
    duration: Optional[int] = 180 # in seconds
    source_type: Optional[str] = "MIDI"
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    # Curriculum ↔ Song System Metadata (Default fallbacks for Null rows)
    educational_category: Optional[str] = "Beginner Foundation"
    learning_objectives: Optional[List[str]] = []
    skills_required: Optional[List[str]] = []
    skills_reinforced: Optional[List[str]] = []
    prerequisite_lesson_slugs: Optional[List[str]] = []
    mastery_threshold_percentage: Optional[float] = 85.0
    ai_coaching_focus: Optional[Dict[str, Any]] = {}
    teacher_notes: Optional[str] = None

    created_at: Optional[datetime] = None

class SongCreate(BaseModel):
    title: str
    composer: Optional[str] = None
    artist: Optional[str] = None
    genre: Optional[str] = None
    difficulty: Optional[str] = "Beginner"
    bpm: Optional[int] = 120
    key_signature: Optional[str] = "C Major"
    time_signature: Optional[str] = "4/4"
    duration: Optional[int] = 180
    source_type: Optional[str] = "MIDI"
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    educational_category: Optional[str] = "Beginner Foundation"
    learning_objectives: Optional[List[str]] = []
    skills_required: Optional[List[str]] = []
    skills_reinforced: Optional[List[str]] = []
    prerequisite_lesson_slugs: Optional[List[str]] = []
    mastery_threshold_percentage: Optional[float] = 85.0
    ai_coaching_focus: Optional[Dict[str, Any]] = {}
    teacher_notes: Optional[str] = None

class SongUpdate(BaseModel):
    title: Optional[str] = None
    composer: Optional[str] = None
    artist: Optional[str] = None
    genre: Optional[str] = None
    difficulty: Optional[str] = None
    bpm: Optional[int] = None
    educational_category: Optional[str] = None

SongDetail = SongSchema
SongSummary = SongSchema
