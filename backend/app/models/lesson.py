import uuid
from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey, DateTime, func, Table, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

# Association table for Many-to-Many relationship between Lessons and Songs
lesson_song = Table(
    'lesson_song',
    Base.metadata,
    Column('lesson_id', UUID(as_uuid=True), ForeignKey('lessons.id', ondelete='CASCADE'), primary_key=True),
    Column('song_id', UUID(as_uuid=True), ForeignKey('songs.id', ondelete='CASCADE'), primary_key=True),
    Column('display_order', Integer, default=0)
)

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
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
    objectives = Column(JSONB, default=list)
    
    visibility = Column(String(50), default="PUBLIC")  # PUBLIC, PRIVATE
    is_published = Column(Boolean, default=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    teacher = relationship("User", back_populates="lessons")
    songs = relationship("Song", secondary=lesson_song, back_populates="lessons")
    progress = relationship("LessonProgress", back_populates="lesson", cascade="all, delete-orphan")
