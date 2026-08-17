from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.json_type import ConditionalUUID

class DifficultyNote(Base):
    """
    DifficultyNote model — individual note in a difficulty variant, linked to source TranscriptionNote.
    """
    __tablename__ = "difficulty_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    difficulty_variant_id = Column(ConditionalUUID, ForeignKey("difficulty_variants.id"), nullable=False, index=True)
    source_note_id = Column(Integer, ForeignKey("transcription_notes.id"), nullable=False) # provenance link
    
    sequence_index = Column(Integer, nullable=False)
    midi_number = Column(Integer, nullable=False)
    note_name = Column(String(10), nullable=False)
    
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    velocity = Column(Integer, default=80)
    
    hand = Column(String(20), default='RIGHT') # LEFT, RIGHT
    measure_number = Column(Integer, nullable=True)
    beat_position = Column(Float, nullable=True)
    importance_score = Column(Float, default=0.5) # used by difficulty engine for note selection

    # Relationships
    difficulty_variant = relationship("DifficultyVariant", back_populates="notes")
    source_note = relationship("TranscriptionNote", back_populates="difficulty_notes")
