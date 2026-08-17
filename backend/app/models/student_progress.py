import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from app.models.json_type import ConditionalUUID
from app.models.json_type import ConditionalJSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class StudentLearningState(Base):
    __tablename__ = "student_learning_states"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(ConditionalUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    current_path_id = Column(ConditionalUUID, nullable=True)
    current_module_id = Column(ConditionalUUID, nullable=True)
    
    # Unlocked and Completed Lists
    unlocked_module_ids = Column(ConditionalJSON, default=list) # e.g. ["mod-1-uuid", "mod-2-uuid"]
    unlocked_lesson_ids = Column(ConditionalJSON, default=list)
    completed_lesson_ids = Column(ConditionalJSON, default=list)
    
    # Adaptive Difficulty Tracking (Step 19)
    # Track per-song, per-difficulty accuracy history to unlock higher levels
    # format: { "song_id": { "EASY": [{ "score": 96, "date": "..." }], "MEDIUM": [] } }
    performance_history = Column(ConditionalJSON, default=dict)
    current_difficulty = Column(String(20), default="EASY")
    
    # Skill Levels & Weak Areas Mapping
    # skill_levels: {"Posture": 90, "SightReading": 75, "Rhythm": 82}
    skill_levels = Column(ConditionalJSON, default=dict)
    
    # weak_areas: [{"measure": 14, "song": "Für Elise", "type": "Rhythm Acceleration"}]
    weak_areas = Column(ConditionalJSON, default=list)
    
    # AI Recommendations & Practice Streak
    ai_recommendations = Column(ConditionalJSON, default=list)
    practice_streak_days = Column(Integer, default=1)
    total_xp = Column(Integer, default=0)

    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="learning_state")
