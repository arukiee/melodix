import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.json_type import ConditionalJSON, ConditionalUUID

class DifficultyVariant(Base):
    """
    DifficultyVariant model — a specific difficulty level derived from a transcription.
    """
    __tablename__ = "difficulty_variants"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    transcription_id = Column(ConditionalUUID, ForeignKey("transcriptions.id"), nullable=False)
    song_id = Column(ConditionalUUID, ForeignKey("songs.id"), nullable=True)
    processing_job_id = Column(ConditionalUUID, ForeignKey("processing_jobs.id"), nullable=False)
    
    level = Column(String(20), nullable=False) # EASY, MEDIUM, HARD, EXPERT
    metrics = Column(ConditionalJSON, default=dict) # DifficultyMetrics
    difficulty_score = Column(Float, default=0.0) # 0.0-1.0 weighted sum
    
    note_count = Column(Integer, default=0)
    tempo_multiplier = Column(Float, default=1.0)
    hands_used = Column(String(20), default='BOTH') # RH, LH, BOTH
    engine_version = Column(String(20), default='1.0.0')
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint('transcription_id', 'level', name='uq_transcription_level'),
    )

    # Relationships
    transcription = relationship("Transcription", back_populates="difficulty_variants")
    processing_job = relationship("ProcessingJob", back_populates="difficulty_variants")
    notes = relationship("DifficultyNote", back_populates="difficulty_variant")
