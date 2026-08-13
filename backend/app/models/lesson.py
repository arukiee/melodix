import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey, DateTime, Table, Index
from app.models.json_type import ConditionalUUID
from app.models.json_type import ConditionalJSON
from sqlalchemy.orm import relationship
from app.core.database import Base

# Association table for Many-to-Many relationship between Lessons and Songs
lesson_song = Table(
    'lesson_song',
    Base.metadata,
    Column('lesson_id', ConditionalUUID, ForeignKey('lessons.id', ondelete='CASCADE'), primary_key=True),
    Column('song_id', ConditionalUUID, ForeignKey('songs.id', ondelete='CASCADE'), primary_key=True),
    Column('display_order', Integer, default=0)
)

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    teacher_id = Column(ConditionalUUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    title = Column(String(255), nullable=False)
    slug = Column(String(300), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    category = Column(String(100), nullable=True, index=True)
    difficulty = Column(String(50), nullable=True, index=True)
    genre = Column(String(100), nullable=True)
    
    estimated_duration = Column(Integer, nullable=True)  # in minutes
    display_order = Column(Integer, default=0)
    thumbnail_url = Column(String(1024), nullable=True)
    
    # Structured objectives: [{"id": "obj-1", "title": "...", "description": "..."}]
    objectives = Column(ConditionalJSON, default=list)
    
    # Structured sections for progressive learning: [{"id": "s-1", "title": "Intro", "start_measure": 0, "end_measure": 8}]
    sections = Column(ConditionalJSON, default=list)
    
    # Structured steps mapping to the 12-stage engine
    steps = Column(ConditionalJSON, default=list)
    
    # Adaptive engine configurations (e.g. {"target_accuracy": 85, "initial_tempo_pct": 50})
    adaptive_thresholds = Column(ConditionalJSON, default=dict)
    
    visibility = Column(String(50), default="PUBLIC")  # PUBLIC, PRIVATE
    is_published = Column(Boolean, default=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    teacher = relationship("User", back_populates="lessons")
    songs = relationship("Song", secondary=lesson_song, back_populates="lessons")
    progress = relationship("LessonProgress", back_populates="lesson", cascade="all, delete-orphan")
