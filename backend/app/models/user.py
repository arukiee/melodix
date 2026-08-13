import uuid
from sqlalchemy import Column, String, Boolean, DateTime, func
from app.models.json_type import ConditionalUUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __table_args__ = {'extend_existing': True}
    __tablename__ = "users"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True) # Nullable for Google OAuth
    full_name = Column(String(255), nullable=False)
    avatar_url = Column(String(1024), nullable=True)
    
    role = Column(String(50), default="STUDENT") # STUDENT, TEACHER, ADMIN
    auth_provider = Column(String(50), default="EMAIL") # EMAIL, GOOGLE
    
    onboarding_completed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: __import__('datetime').datetime.now(__import__('datetime').timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: __import__('datetime').datetime.now(__import__('datetime').timezone.utc), onupdate=lambda: __import__('datetime').datetime.now(__import__('datetime').timezone.utc))

    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    lessons = relationship("Lesson", back_populates="teacher")
    lesson_progress = relationship("LessonProgress", back_populates="user", cascade="all, delete-orphan")
