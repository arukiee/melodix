import uuid
from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True) # Nullable for Google OAuth
    full_name = Column(String(255), nullable=False)
    avatar_url = Column(String(1024), nullable=True)
    
    role = Column(String(50), default="STUDENT") # STUDENT, TEACHER, ADMIN
    auth_provider = Column(String(50), default="EMAIL") # EMAIL, GOOGLE
    
    onboarding_completed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    lessons = relationship("Lesson", back_populates="teacher")
    lesson_progress = relationship("LessonProgress", back_populates="user", cascade="all, delete-orphan")
