import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class StudentLearningState(Base):
    __tablename__ = "student_learning_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    current_path_id = Column(UUID(as_uuid=True), nullable=True)
    current_module_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Unlocked and Completed Lists
    unlocked_module_ids = Column(JSONB, default=list) # e.g. ["mod-1-uuid", "mod-2-uuid"]
    unlocked_lesson_ids = Column(JSONB, default=list)
    completed_lesson_ids = Column(JSONB, default=list)
    
    # Skill Levels & Weak Areas Mapping
    # skill_levels: {"Posture": 90, "SightReading": 75, "Rhythm": 82}
    skill_levels = Column(JSONB, default=dict)
    
    # weak_areas: [{"measure": 14, "song": "Für Elise", "type": "Rhythm Acceleration"}]
    weak_areas = Column(JSONB, default=list)
    
    # AI Recommendations & Practice Streak
    ai_recommendations = Column(JSONB, default=list)
    practice_streak_days = Column(Integer, default=1)
    total_xp = Column(Integer, default=0)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", backref="learning_state")
