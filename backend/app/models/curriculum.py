import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey, DateTime, Float
from app.models.json_type import ConditionalUUID, ConditionalJSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    slug = Column(String(300), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    target_role = Column(String(50), default="STUDENT") # STUDENT, TEACHER
    display_order = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    modules = relationship("CurriculumModule", back_populates="path", cascade="all, delete-orphan", order_by="CurriculumModule.display_order")

class CurriculumModule(Base):
    __tablename__ = "curriculum_modules"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    path_id = Column(ConditionalUUID, ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    slug = Column(String(300), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=0)
    is_unlocked_by_default = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    path = relationship("LearningPath", back_populates="modules")
    units = relationship("CurriculumUnit", back_populates="module", cascade="all, delete-orphan", order_by="CurriculumUnit.display_order")
    checkpoint = relationship("CurriculumCheckpoint", back_populates="module", uselist=False, cascade="all, delete-orphan")

class CurriculumUnit(Base):
    __tablename__ = "curriculum_units"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    module_id = Column(ConditionalUUID, ForeignKey("curriculum_modules.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    slug = Column(String(300), nullable=False, index=True)
    display_order = Column(Integer, default=0)

    module = relationship("CurriculumModule", back_populates="units")
    lessons = relationship("CurriculumLesson", back_populates="unit", cascade="all, delete-orphan", order_by="CurriculumLesson.display_order")

class CurriculumLesson(Base):
    __tablename__ = "curriculum_lessons"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    unit_id = Column(ConditionalUUID, ForeignKey("curriculum_units.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    slug = Column(String(300), unique=True, nullable=False, index=True)
    learning_goal = Column(Text, nullable=True)
    estimated_time = Column(Integer, default=15) # in minutes
    difficulty = Column(String(50), default="BEGINNER")
    
    # Metadata for adaptive AI & Prerequisites
    required_skills = Column(ConditionalJSON, default=list) # e.g. ["Posture", "Middle C"]
    skills_taught = Column(ConditionalJSON, default=list)   # e.g. ["Finger Independence", "Legato"]
    objective = Column(ConditionalJSON, nullable=True)  # e.g., {"type": "note", "value": "C4"}
    prerequisites = Column(ConditionalJSON, default=list)   # e.g. ["keyboard-foundations"]
    
    xp_reward = Column(Integer, default=100)
    ai_coaching_enabled = Column(Boolean, default=True)
    teacher_assignable = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    unit = relationship("CurriculumUnit", back_populates="lessons")
    exercises = relationship("CurriculumExercise", back_populates="lesson", cascade="all, delete-orphan", order_by="CurriculumExercise.display_order")

class CurriculumExercise(Base):
    __tablename__ = "curriculum_exercises"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    lesson_id = Column(ConditionalUUID, ForeignKey("curriculum_lessons.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    exercise_type = Column(String(50), default="PRACTICE") # DRILL, QUIZ, REPERTOIRE
    tempo_bpm = Column(Integer, default=80)
    key_signature = Column(String(20), default="C Major")
    midi_uri = Column(String(1024), nullable=True)
    display_order = Column(Integer, default=0)

    lesson = relationship("CurriculumLesson", back_populates="exercises")

class CurriculumCheckpoint(Base):
    __tablename__ = "curriculum_checkpoints"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    module_id = Column(ConditionalUUID, ForeignKey("curriculum_modules.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    pass_threshold_percentage = Column(Float, default=80.0)
    unlocks_module_id = Column(ConditionalUUID, nullable=True)

    module = relationship("CurriculumModule", back_populates="checkpoint")
