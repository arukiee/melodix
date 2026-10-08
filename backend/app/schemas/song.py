from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class SongSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    composer: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    mood: Optional[str] = None
    language: Optional[str] = None
    difficulty: Optional[str] = "Beginner"
    bpm: Optional[int] = 120
    tempo: Optional[int] = None
    key_signature: Optional[str] = "C Major"
    key: Optional[str] = None
    time_signature: Optional[str] = "4/4"
    duration: Optional[int] = 180
    source_type: Optional[str] = "MIDI"
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    artwork_url: Optional[str] = None
    artwork: Optional[str] = None
    skills: Optional[List[str]] = []
    available_arrangements: Optional[List[str]] = ["Easy", "Medium", "Hard"]
    is_learnable: Optional[bool] = True
    learnable_status: Optional[str] = "learnable"

    educational_category: Optional[str] = "Beginner Foundation"
    learning_objectives: Optional[List[str]] = []
    skills_required: Optional[List[str]] = []
    skills_reinforced: Optional[List[str]] = []
    prerequisite_lesson_slugs: Optional[List[str]] = []
    mastery_threshold_percentage: Optional[float] = 85.0
    ai_coaching_focus: Optional[Dict[str, Any]] = {}
    teacher_notes: Optional[str] = None

    created_at: Optional[datetime] = None
    saved: Optional[bool] = False
    reason: Optional[str] = None
    progress_percentage: Optional[float] = None
    completed: Optional[bool] = None
    current_mission_id: Optional[str] = None
    last_score: Optional[Dict[str, Any]] = None


class SongCreate(BaseModel):
    title: str
    composer: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    mood: Optional[str] = None
    language: Optional[str] = None
    difficulty: Optional[str] = "Beginner"
    bpm: Optional[int] = 120
    tempo: Optional[int] = None
    key_signature: Optional[str] = "C Major"
    time_signature: Optional[str] = "4/4"
    duration: Optional[int] = 180
    source_type: Optional[str] = "MIDI"
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    artwork_url: Optional[str] = None
    skills: Optional[List[str]] = []
    available_arrangements: Optional[List[str]] = ["Easy", "Medium", "Hard"]
    is_learnable: Optional[bool] = True
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
    album: Optional[str] = None
    genre: Optional[str] = None
    mood: Optional[str] = None
    language: Optional[str] = None
    difficulty: Optional[str] = None
    bpm: Optional[int] = None
    tempo: Optional[int] = None
    skills: Optional[List[str]] = None
    available_arrangements: Optional[List[str]] = None
    is_learnable: Optional[bool] = None
    educational_category: Optional[str] = None


class CatalogSearchResult(SongSchema):
    rank_score: float = 0.0


class AutocompleteSuggestion(BaseModel):
    id: UUID
    title: str
    artist: Optional[str] = None
    artwork: Optional[str] = None


class DiscoveryRow(BaseModel):
    id: str
    title: str
    songs: List[SongSchema] = Field(default_factory=list)


class DiscoveryHomeResponse(BaseModel):
    rows: List[DiscoveryRow]


class SemanticSearchResponse(BaseModel):
    query: str
    mode: str
    results: List[SongSchema]


class AssignSongRequest(BaseModel):
    class_id: Optional[UUID] = None
    class_name: Optional[str] = None


class ClassroomSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str


class StartLearningRequest(BaseModel):
    arrangement: str = "Easy"


SongDetail = SongSchema
SongSummary = SongSchema
