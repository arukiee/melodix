import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from app.models.json_type import ConditionalJSON, ConditionalUUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.lesson import lesson_song

class Song(Base):
    __tablename__ = "songs"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    
    title = Column(String(255), nullable=False, index=True)
    composer = Column(String(255), nullable=True)
    artist = Column(String(255), nullable=True)
    genre = Column(String(100), nullable=True)
    difficulty = Column(String(50), nullable=True, index=True)
    
    bpm = Column(Integer, nullable=True)
    key_signature = Column(String(20), nullable=True)
    time_signature = Column(String(20), nullable=True)
    duration = Column(Integer, nullable=True) # in seconds
    
    source_type = Column(String(50), nullable=True) # MIDI, MUSICXML
    file_url = Column(String(1024), nullable=True)
    thumbnail_url = Column(String(1024), nullable=True)

    educational_category = Column(String(100), default="Beginner Foundation", index=True)
    learning_objectives = Column(ConditionalJSON, default=list)  # e.g. ["Master 3/4 waltz rhythm", "Execute smooth legato phrasing"]
    skills_required = Column(ConditionalJSON, default=list)      # e.g. ["5-Finger Position", "Treble Staff"]
    skills_reinforced = Column(ConditionalJSON, default=list)    # e.g. ["Hands Together", "Waltz Meter"]
    prerequisite_lesson_slugs = Column(ConditionalJSON, default=list) # e.g. ["minuet-in-g-section-a"]
    mastery_threshold_percentage = Column(Float, default=85.0)
    missions = Column(ConditionalJSON, default=list)             # Structured learning tasks per hand/phrase
    sections = Column(ConditionalJSON, default=list)
    steps = Column(ConditionalJSON, default=list)
    adaptive_thresholds = Column(ConditionalJSON, default=dict)
    
    # Structured AI Evaluation Criteria
    # ai_coaching_focus: {
    #   "primary_skills": ["Rhythm", "Legato"],
    #   "common_errors": ["Rushing measure 8", "Weak left hand drone chord"],
    #   "feedback_priorities": ["Timing", "Dynamics", "Fingering"]
    # }
    ai_coaching_focus = Column(ConditionalJSON, default=dict)
    teacher_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    lessons = relationship("Lesson", secondary=lesson_song, back_populates="songs")
