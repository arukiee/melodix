import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.json_type import ConditionalJSON, ConditionalUUID

class ProcessingProvenance(Base):
    """
    ProcessingProvenance model — full traceability record.
    """
    __tablename__ = "processing_provenances"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    processing_job_id = Column(ConditionalUUID, ForeignKey("processing_jobs.id"), nullable=False, unique=True)
    song_id = Column(ConditionalUUID, ForeignKey("songs.id"), nullable=True)
    audio_asset_id = Column(ConditionalUUID, ForeignKey("audio_assets.id"), nullable=False)
    transcription_id = Column(ConditionalUUID, ForeignKey("transcriptions.id"), nullable=True)
    
    pipeline_version = Column(String(20), nullable=False)
    source_type = Column(String(50), nullable=False)
    file_hash = Column(String(64), nullable=False)
    audio_duration = Column(Float, nullable=True)
    
    transcription_model = Column(String(100), nullable=True)
    transcription_model_version = Column(String(50), nullable=True)
    bpm_engine_version = Column(String(20), nullable=True)
    difficulty_engine_version = Column(String(20), nullable=True)
    
    tempo_value = Column(Float, nullable=True)
    tempo_confidence = Column(Float, nullable=True) # Melodix-computed
    note_count = Column(Integer, nullable=True)
    
    difficulty_variants_summary = Column(ConditionalJSON, default=dict) # {easy: 120, medium: 280, ...}
    artifact_paths = Column(ConditionalJSON, default=dict) # MinIO paths to all raw artifacts
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    processing_job = relationship("ProcessingJob", back_populates="provenance")
