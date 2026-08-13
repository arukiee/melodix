import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime, Float
from app.models.json_type import ConditionalUUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(ConditionalUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(ConditionalUUID, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)

    progress_percentage = Column(Float, default=0.0)  # 0.0 to 100.0
    completed = Column(Boolean, default=False)
    last_opened = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="lesson_progress")
    lesson = relationship("Lesson", back_populates="progress")
