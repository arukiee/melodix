from pydantic import BaseModel, Field
from typing import Optional, List, Any
import uuid
from datetime import datetime

class Objective(BaseModel):
    id: str
    title: str
    description: Optional[str] = None

class LessonStepSchema(BaseModel):
    id: str
    title: str
    type: str
    description: Optional[str] = None
    measures: List[int] = []
    completed: bool = False
    locked: bool = False

class LessonBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    difficulty: Optional[str] = Field(None, pattern="^(BEGINNER|INTERMEDIATE|ADVANCED)$")
    genre: Optional[str] = Field(None, max_length=100)
    estimated_duration: Optional[int] = Field(None, gt=0)
    display_order: int = 0
    thumbnail_url: Optional[str] = Field(None, max_length=1024)
    objectives: List[Objective] = []
    steps: List[LessonStepSchema] = []
    adaptive_thresholds: dict = {}
    visibility: str = Field("PUBLIC", pattern="^(PUBLIC|PRIVATE)$")

class LessonCreate(LessonBase):
    slug: Optional[str] = Field(None, min_length=1, max_length=300)
    is_published: bool = False

class LessonUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    difficulty: Optional[str] = Field(None, pattern="^(BEGINNER|INTERMEDIATE|ADVANCED)$")
    genre: Optional[str] = Field(None, max_length=100)
    estimated_duration: Optional[int] = Field(None, gt=0)
    display_order: Optional[int] = None
    thumbnail_url: Optional[str] = Field(None, max_length=1024)
    objectives: Optional[List[Objective]] = None
    steps: Optional[List[LessonStepSchema]] = None
    adaptive_thresholds: Optional[dict] = None
    visibility: Optional[str] = Field(None, pattern="^(PUBLIC|PRIVATE)$")
    is_published: Optional[bool] = None

class TeacherSummary(BaseModel):
    id: uuid.UUID
    full_name: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

class LessonResponse(LessonBase):
    id: uuid.UUID
    slug: str
    teacher_id: Optional[uuid.UUID] = None
    teacher: Optional[TeacherSummary] = None
    is_published: bool
    published_at: Optional[datetime] = None
    songs_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class LessonListResponse(BaseModel):
    items: List[LessonResponse]
    total: int
    page: int
    page_size: int

class LessonProgressUpdate(BaseModel):
    progress_percentage: float = Field(..., ge=0.0, le=100.0)

class LessonProgressResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    lesson_id: uuid.UUID
    progress_percentage: float
    completed: bool
    last_opened: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
