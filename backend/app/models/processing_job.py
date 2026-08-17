import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.json_type import ConditionalJSON, ConditionalUUID

class ProcessingJobStage(str, enum.Enum):
    QUEUED = "QUEUED"
    VALIDATING = "VALIDATING"
    PREPROCESSING = "PREPROCESSING"
    TRANSCRIBING = "TRANSCRIBING"
    VALIDATING_NOTES = "VALIDATING_NOTES"
    ANALYZING_RHYTHM = "ANALYZING_RHYTHM"
    ANALYZING_CHORDS = "ANALYZING_CHORDS"
    ASSIGNING_HANDS = "ASSIGNING_HANDS"
    COMPUTING_DIFFICULTY = "COMPUTING_DIFFICULTY"
    CREATING_LESSON = "CREATING_LESSON"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ProcessingJob(Base):
    """
    ProcessingJob model — central pipeline tracking entity.
    """
    __tablename__ = "processing_jobs"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    audio_asset_id = Column(ConditionalUUID, ForeignKey("audio_assets.id"), nullable=False)
    song_id = Column(ConditionalUUID, ForeignKey("songs.id"), nullable=True)
    user_id = Column(ConditionalUUID, ForeignKey("users.id"), nullable=False)
    
    status = Column(String(50), default=ProcessingJobStage.QUEUED.value)
    progress_percent = Column(Integer, default=0)
    pipeline_version = Column(String(20), default='1.0.0')
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    stage_log = Column(ConditionalJSON, default=list) # [{stage, started_at, completed_at, result}]
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    audio_asset = relationship("AudioAsset", back_populates="processing_jobs")
    transcription = relationship("Transcription", uselist=False, back_populates="processing_job")
    difficulty_variants = relationship("DifficultyVariant", back_populates="processing_job")
    provenance = relationship("ProcessingProvenance", uselist=False, back_populates="processing_job")
