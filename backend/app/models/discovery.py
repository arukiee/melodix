import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Float, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.json_type import ConditionalUUID


class SavedSong(Base):
    __tablename__ = "saved_songs"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(ConditionalUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    song_id = Column(ConditionalUUID, ForeignKey("songs.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("user_id", "song_id", name="uq_saved_song_user"),)

    user = relationship("User", foreign_keys=[user_id])
    song = relationship("Song", foreign_keys=[song_id])


class SongLearningProgress(Base):
    __tablename__ = "song_learning_progress"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(ConditionalUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    song_id = Column(ConditionalUUID, ForeignKey("songs.id", ondelete="CASCADE"), nullable=False, index=True)
    arrangement = Column(String(20), default="Easy")
    progress_percentage = Column(Float, default=0.0)
    completed = Column(Boolean, default=False)
    last_played_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("user_id", "song_id", name="uq_song_learning_user"),)

    user = relationship("User", foreign_keys=[user_id])
    song = relationship("Song", foreign_keys=[song_id])


class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    teacher_id = Column(ConditionalUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    teacher = relationship("User", foreign_keys=[teacher_id])
    memberships = relationship("ClassMembership", back_populates="classroom", cascade="all, delete-orphan")
    assignments = relationship("ClassSongAssignment", back_populates="classroom", cascade="all, delete-orphan")


class ClassMembership(Base):
    __tablename__ = "class_memberships"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    class_id = Column(ConditionalUUID, ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(ConditionalUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("class_id", "user_id", name="uq_class_member"),)

    classroom = relationship("Classroom", back_populates="memberships")
    user = relationship("User", foreign_keys=[user_id])


class ClassSongAssignment(Base):
    __tablename__ = "class_song_assignments"

    id = Column(ConditionalUUID, primary_key=True, default=uuid.uuid4)
    class_id = Column(ConditionalUUID, ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False, index=True)
    song_id = Column(ConditionalUUID, ForeignKey("songs.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by = Column(ConditionalUUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    classroom = relationship("Classroom", back_populates="assignments")
    song = relationship("Song", foreign_keys=[song_id])
