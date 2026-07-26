import uuid
from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.lesson import lesson_song

class Song(Base):
    __tablename__ = "songs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    title = Column(String(255), nullable=False)
    composer = Column(String(255), nullable=True)
    artist = Column(String(255), nullable=True)
    genre = Column(String(100), nullable=True)
    difficulty = Column(String(50), nullable=True)
    
    bpm = Column(Integer, nullable=True)
    key_signature = Column(String(20), nullable=True)
    time_signature = Column(String(20), nullable=True)
    duration = Column(Integer, nullable=True) # in seconds
    
    source_type = Column(String(50), nullable=True) # MIDI, MUSICXML
    file_url = Column(String(1024), nullable=True)
    thumbnail_url = Column(String(1024), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    lessons = relationship("Lesson", secondary=lesson_song, back_populates="songs")
