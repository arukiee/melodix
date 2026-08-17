import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.json_type import ConditionalJSON, ConditionalUUID

class AudioAsset(Base):
    """
    AudioAsset model — stores uploaded audio files with provenance.
    """
    __tablename__ = "audio_assets"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(ConditionalUUID, ForeignKey("users.id"), nullable=False)
    song_id = Column(ConditionalUUID, ForeignKey("songs.id"), nullable=True)
    
    source_type = Column(String(50)) # USER_UPLOAD, USER_MIDI, PUBLIC_DOMAIN, LICENSED
    original_filename = Column(String(512), nullable=False)
    file_hash_sha256 = Column(String(64), unique=True, nullable=False)
    storage_path = Column(String(1024), nullable=False) # MinIO path like audio/{id}/original.wav
    format = Column(String(20), nullable=False) # wav, mp3, flac, mid, ogg, m4a
    
    duration_seconds = Column(Float, nullable=True) # computed after validation
    sample_rate = Column(Integer, nullable=True)
    channels = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=False)
    
    is_valid = Column(Boolean, default=False)
    validation_errors = Column(ConditionalJSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    processing_jobs = relationship("ProcessingJob", back_populates="audio_asset")
    transcriptions = relationship("Transcription", back_populates="audio_asset")
