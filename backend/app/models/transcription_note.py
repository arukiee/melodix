from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.json_type import ConditionalUUID

class TranscriptionNote(Base):
    """
    TranscriptionNote model — canonical Melodix note representation.
    """
    __tablename__ = "transcription_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transcription_id = Column(ConditionalUUID, ForeignKey("transcriptions.id"), nullable=False, index=True)
    
    sequence_index = Column(Integer, nullable=False)
    midi_number = Column(Integer, nullable=False) # 0-127
    note_name = Column(String(10), nullable=False) # 'C4', 'E4'
    
    start_time = Column(Float, nullable=False) # seconds
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    velocity = Column(Integer, default=80) # 0-127
    confidence = Column(Float, default=0.0) # Melodix-computed from model activation data
    
    is_validated = Column(Boolean, default=False)
    validation_action = Column(String(20), nullable=True) # KEEP, MERGE, DISCARD, FLAG
    validation_reason = Column(String(500), nullable=True)
    
    hand = Column(String(20), default='UNASSIGNED') # LEFT, RIGHT, UNASSIGNED
    measure_number = Column(Integer, nullable=True)
    beat_position = Column(Float, nullable=True)

    # Relationships
    transcription = relationship("Transcription", back_populates="notes")
    difficulty_notes = relationship("DifficultyNote", back_populates="source_note")
