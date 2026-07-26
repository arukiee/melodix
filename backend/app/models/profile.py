import uuid
from sqlalchemy import Column, String, Integer, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    bio = Column(Text, nullable=True)
    skill_level = Column(String(50), default="BEGINNER")
    preferred_instrument = Column(String(100), default="Piano")
    daily_practice_goal = Column(Integer, default=30) # in minutes
    
    preferred_genres = Column(JSONB, default=list)
    learning_preferences = Column(JSONB, default=dict)

    # Relationships
    user = relationship("User", back_populates="profile")
