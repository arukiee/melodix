import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.json_type import ConditionalUUID

class Transcription(Base):
    """
    Transcription model — stores Basic Pitch transcription results.
    """
    __tablename__ = "transcriptions"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    processing_job_id = Column(ConditionalUUID, ForeignKey("processing_jobs.id"), nullable=False, unique=True)
    audio_asset_id = Column(ConditionalUUID, ForeignKey("audio_assets.id"), nullable=False)
    song_id = Column(ConditionalUUID, ForeignKey("songs.id"), nullable=True)
    
    model_name = Column(String(100), default='basic-pitch')
    model_version = Column(String(50), nullable=False)
    
    raw_midi_path = Column(String(1024), nullable=True) # MinIO path
    model_output_path = Column(String(1024), nullable=True) # MinIO path for .npz
    note_events_path = Column(String(1024), nullable=True) # MinIO path for .csv
    
    note_count = Column(Integer, default=0)
    duration_seconds = Column(Float, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    notes = relationship("TranscriptionNote", back_populates="transcription")
    processing_job = relationship("ProcessingJob", back_populates="transcription")
    audio_asset = relationship("AudioAsset", back_populates="transcriptions")
    difficulty_variants = relationship("DifficultyVariant", back_populates="transcription")
