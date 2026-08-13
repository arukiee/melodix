# backend/app/models/progress_state.py

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from app.models.json_type import ConditionalUUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class ProgressState(Base):
    __tablename__ = "progress_state"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(ConditionalUUID, ForeignKey("users.id"), nullable=False, index=True)
    lesson_id = Column(ConditionalUUID, ForeignKey("curriculum_lessons.id"), nullable=False, index=True)
    last_note_index = Column(Integer, default=0)
    attempts = Column(Integer, default=0)
    confidence = Column(Float, default=0.0)
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # relationships
    lesson = relationship("CurriculumLesson", backref="progress_entries")
    # user relationship assumed in users model
