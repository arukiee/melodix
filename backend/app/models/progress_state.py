# backend/app/models/progress_state.py

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class ProgressState(Base):
    __tablename__ = "progress_state"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("curriculum_lessons.id"), nullable=False, index=True)
    last_note_index = Column(Integer, default=0)
    attempts = Column(Integer, default=0)
    confidence = Column(Float, default=0.0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # relationships
    lesson = relationship("CurriculumLesson", backref="progress_entries")
    # user relationship assumed in users model
