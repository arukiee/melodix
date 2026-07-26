# -*- coding: utf-8 -*-
"""SQLAlchemy 2.x typed ORM models for the Songs domain (Phase 10).
This file defines:
* Common mixins (TimestampMixin, SoftDeleteMixin)
* Python Enums that map to PostgreSQL ENUM types
* Lookup tables (Instrument, Genre, Language, Technique, Articulation, DynamicMarking, ErrorType, Skill)
* Core song tables and relationships (Song, SongFile, SongDifficulty, SongTechnique, SongSkill association, SongEvent,
  SongGroundTruthMeta, SongAnalytics)
The models closely follow the Alembic migration created in Step 1 and use typed
`Mapped`/`mapped_column` declarations.
"""

from __future__ import annotations

import enum
from typing import List, Optional

from sqlalchemy import (
    BOOLEAN,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    selectinload,
)

# ---------------------------------------------------------------------------
# Base & Mixins
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """Base declarative class used throughout the project."""
    pass


class TimestampMixin:
    """Add created_at and updated_at columns with server defaults.
    updated_at is automatically refreshed on UPDATE via onupdate.
    """

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True, index=True
    )


class SoftDeleteMixin:
    """Add a nullable deleted_at column for soft‑deletion.
    The actual delete operation is handled at the repository level; ORM
    cascades remain unchanged.
    """

    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


# ---------------------------------------------------------------------------
# Enum definitions (Python <-> PostgreSQL)
# ---------------------------------------------------------------------------

class FileTypeEnum(str, enum.Enum):
    MUSICXML = "musicxml"
    MIDI = "midi"
    PDF = "pdf"
    AUDIO = "audio"


class StatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    FAILED = "FAILED"


class ProcessingStateEnum(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    ERROR = "ERROR"


class DifficultyLevelEnum(str, enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    PROFESSIONAL = "PROFESSIONAL"


# ---------------------------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------------------------

class Instrument(Base, TimestampMixin):
    __tablename__ = "instrument"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    family: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    __table_args__ = (Index("ix_instrument_name", "name"),)

    def __repr__(self) -> str:
        return f"<Instrument id={self.id} name={self.name}>"


class Genre(Base, TimestampMixin):
    __tablename__ = "genre"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    __table_args__ = (Index("ix_genre_name", "name"),)

    def __repr__(self) -> str:
        return f"<Genre id={self.id} name={self.name}>"


class Language(Base, TimestampMixin):
    __tablename__ = "language"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    __table_args__ = (Index("ix_language_name", "name"),)

    def __repr__(self) -> str:
        return f"<Language id={self.id} name={self.name}>"


class Technique(Base, TimestampMixin):
    __tablename__ = "technique"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    __table_args__ = (Index("ix_technique_name", "name"),)

    def __repr__(self) -> str:
        return f"<Technique id={self.id} name={self.name}>"


class Articulation(Base, TimestampMixin):
    __tablename__ = "articulation"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    __table_args__ = (Index("ix_articulation_name", "name"),)

    def __repr__(self) -> str:
        return f"<Articulation id={self.id} name={self.name}>"


class DynamicMarking(Base, TimestampMixin):
    __tablename__ = "dynamic_marking"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    __table_args__ = (Index("ix_dynamic_code", "code"),)

    def __repr__(self) -> str:
        return f"<DynamicMarking id={self.id} code={self.code}>"


class ErrorType(Base, TimestampMixin):
    __tablename__ = "error_type"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    __table_args__ = (Index("ix_error_type_name", "name"),)

    def __repr__(self) -> str:
        return f"<ErrorType id={self.id} name={self.name}>"


class Skill(Base, TimestampMixin):
    __tablename__ = "skill"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Back‑reference to songs – many‑to‑many via song_skill association
    songs: Mapped[List["Song"]] = relationship(
        "Song", secondary="song_skill", back_populates="skills", lazy="selectin"
    )

    __table_args__ = (Index("ix_skill_name", "name"),)

    def __repr__(self) -> str:
        return f"<Skill id={self.id} name={self.name}>"


# ---------------------------------------------------------------------------
# Association tables (explicit Table objects for many‑to‑many)
# ---------------------------------------------------------------------------

song_skill = Table(
    "song_skill",
    Base.metadata,
    Column("song_id", Integer, ForeignKey("song.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skill.id"), primary_key=True),
    Column("importance_level", Integer, nullable=False),
)

# ---------------------------------------------------------------------------
# Core Song domain models
# ---------------------------------------------------------------------------

class Song(Base, TimestampMixin, SoftDeleteMixin):
    """Canonical representation of a musical piece.
    Includes metadata required for search, recommendations and the Adaptive
    Music Performance Assessment Engine.
    """

    __tablename__ = "song"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    composer: Mapped[str] = mapped_column(String, nullable=False)
    arranger: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    copyright: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    genre_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("genre.id"), nullable=True)
    language_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("language.id"), nullable=True)
    instrument_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("instrument.id"), nullable=True)
    key_signature: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    time_signature: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    default_tempo_bpm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Numeric(10, 3), nullable=True)
    difficulty_override: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thumbnail_uri: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    preview_audio_uri: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    lyrics_available: Mapped[bool] = mapped_column(BOOLEAN, server_default=text("FALSE"))
    is_public: Mapped[bool] = mapped_column(BOOLEAN, server_default=text("TRUE"))
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    published_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ---------------- Relationships ----------------
    files: Mapped[List["SongFile"]] = relationship(
        "SongFile",
        back_populates="song",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    difficulty: Mapped["SongDifficulty"] = relationship(
        "SongDifficulty",
        uselist=False,
        back_populates="song",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    techniques: Mapped[List["SongTechnique"]] = relationship(
        "SongTechnique",
        back_populates="song",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    skills: Mapped[List[Skill]] = relationship(
        "Skill", secondary=song_skill, back_populates="songs", lazy="selectin"
    )

    events: Mapped[List["SongEvent"]] = relationship(
        "SongEvent",
        back_populates="song",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    ground_truth_meta: Mapped["SongGroundTruthMeta"] = relationship(
        "SongGroundTruthMeta",
        uselist=False,
        back_populates="song",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    analytics: Mapped["SongAnalytics"] = relationship(
        "SongAnalytics",
        uselist=False,
        back_populates="song",
        lazy="joined",
    )

    __table_args__ = (
        Index("ix_song_genre", "genre_id"),
        Index("ix_song_instrument", "instrument_id"),
        Index("ix_song_key_sig", "key_signature"),
        Index("ix_song_public", "is_public"),
    )

    def __repr__(self) -> str:
        return f"<Song id={self.id} title={self.title}>"


class SongFile(Base, TimestampMixin):
    """Versioned asset for a Song (MusicXML, MIDI, PDF, audio)."""

    __tablename__ = "song_file"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    song_id: Mapped[int] = mapped_column(Integer, ForeignKey("song.id", ondelete="CASCADE"), nullable=False)
    file_type: Mapped[FileTypeEnum] = mapped_column(
        PG_ENUM(*[e.value for e in FileTypeEnum], name="file_type"),
        nullable=False,
    )
    uri: Mapped[str] = mapped_column(String, nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    status: Mapped[StatusEnum] = mapped_column(
        PG_ENUM(*[e.value for e in StatusEnum], name="status"), nullable=False, server_default=text("'ACTIVE'")
    )
    uploaded_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    processing_state: Mapped[ProcessingStateEnum] = mapped_column(
        PG_ENUM(*[e.value for e in ProcessingStateEnum], name="processing_state"),
        nullable=False,
        server_default=text("'PENDING'")
    )
    uploaded_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_primary: Mapped[bool] = mapped_column(BOOLEAN, server_default=text("FALSE"))

    song: Mapped[Song] = relationship("Song", back_populates="files")

    __table_args__ = (
        UniqueConstraint("song_id", "file_type", name="uq_song_file_primary", condition=text("is_primary")),
    )

    def __repr__(self) -> str:
        return f"<SongFile id={self.id} song_id={self.song_id} type={self.file_type}>"


class SongDifficulty(Base, TimestampMixin):
    """Extended difficulty metadata used by adaptive recommendation.
    One‑to‑one relationship with :class:`Song`.
    """

    __tablename__ = "song_difficulty"

    song_id: Mapped[int] = mapped_column(Integer, ForeignKey("song.id", ondelete="CASCADE"), primary_key=True)
    difficulty_level: Mapped[DifficultyLevelEnum] = mapped_column(
        PG_ENUM(*[e.value for e in DifficultyLevelEnum], name="difficulty_level"), nullable=False
    )
    estimated_tempo_bpm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    polyphony_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    hand_span_mm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pedal_usage: Mapped[Optional[bool]] = mapped_column(BOOLEAN, nullable=True)
    ornamentation_complexity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    finger_independence_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    chord_complexity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rhythmic_complexity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sight_reading_difficulty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    technique_density: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expression_complexity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    song: Mapped[Song] = relationship("Song", back_populates="difficulty", uselist=False)

    def __repr__(self) -> str:
        return f"<SongDifficulty song_id={self.song_id} level={self.difficulty_level}>"


class SongTechnique(Base, TimestampMixin):
    """Specific technique requirements for a Song (many‑to‑one)."""

    __tablename__ = "song_technique"
    __table_args__ = (UniqueConstraint("song_id", "technique_id", name="uq_song_technique"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    song_id: Mapped[int] = mapped_column(Integer, ForeignKey("song.id", ondelete="CASCADE"), nullable=False)
    technique_id: Mapped[int] = mapped_column(Integer, ForeignKey("technique.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    song: Mapped[Song] = relationship("Song", back_populates="techniques")
    technique: Mapped[Technique] = relationship("Technique", lazy="joined")

    def __repr__(self) -> str:
        return f"<SongTechnique song_id={self.song_id} technique_id={self.technique_id}>"


class SongEvent(Base, TimestampMixin):
    """Canonical ground‑truth musical event.
    Each row represents a single note/rest together with expressive attributes.
    """

    __tablename__ = "song_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    song_id: Mapped[int] = mapped_column(Integer, ForeignKey("song.id", ondelete="CASCADE"), nullable=False)
    measure: Mapped[int] = mapped_column(Integer, nullable=False)
    beat: Mapped[float] = mapped_column(Numeric(5, 3), nullable=False)
    tick: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    note_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_rest: Mapped[bool] = mapped_column(BOOLEAN, server_default=text("FALSE"))
    pitch: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    midi_note: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    onset_sec: Mapped[float] = mapped_column(Float, nullable=False)
    duration_sec: Mapped[float] = mapped_column(Float, nullable=False)
    velocity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    chord_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    voice: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    hand: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    articulation_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("articulation.id"), nullable=True)
    dynamic_marking_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("dynamic_marking.id"), nullable=True)
    expected_fingering: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phrase_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    slur_group: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tie_group: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ornament_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    song: Mapped[Song] = relationship("Song", back_populates="events")
    articulation: Mapped[Optional[Articulation]] = relationship(lazy="joined")
    dynamic_marking: Mapped[Optional[DynamicMarking]] = relationship(lazy="joined")

    __table_args__ = (
        Index("ix_song_event_song_measure", "song_id", "measure"),
        Index("ix_song_event_song_onset", "song_id", "onset_sec"),
        Index("ix_song_event_note_index", "song_id", "note_index"),
    )

    def __repr__(self) -> str:
        return f"<SongEvent id={self.id} song_id={self.song_id} measure={self.measure} beat={self.beat}>"


class SongGroundTruthMeta(Base, TimestampMixin):
    """Metadata about how the canonical ground‑truth timeline was generated."""

    __tablename__ = "song_ground_truth_meta"

    song_id: Mapped[int] = mapped_column(Integer, ForeignKey("song.id", ondelete="CASCADE"), primary_key=True)
    generated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    generator_version: Mapped[str] = mapped_column(String, nullable=False)
    parser_version: Mapped[str] = mapped_column(String, nullable=False)
    source_file_id: Mapped[int] = mapped_column(Integer, ForeignKey("song_file.id"), nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    validation_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    generated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    processing_duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    song: Mapped[Song] = relationship("Song", back_populates="ground_truth_meta", uselist=False)
    source_file: Mapped[SongFile] = relationship(lazy="joined")

    def __repr__(self) -> str:
        return f"<SongGroundTruthMeta song_id={self.song_id} generated_at={self.generated_at}>"


class SongAnalytics(Base, TimestampMixin):
    """Aggregated performance analytics for a Song.
    Updated asynchronously by background workers.
    """

    __tablename__ = "song_analytics"

    song_id: Mapped[int] = mapped_column(Integer, ForeignKey("song.id", ondelete="CASCADE"), primary_key=True)
    avg_pitch_accuracy: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    avg_timing_accuracy: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    avg_rhythm_accuracy: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    avg_ioi_accuracy: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    avg_tempo_stability: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    avg_duration_accuracy: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    avg_chord_accuracy: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    avg_dynamics_accuracy: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    total_practice_sessions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_unique_students: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    average_completion_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    average_mastery_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    most_common_error_type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("error_type.id"), nullable=True)
    recommendation_success_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)

    song: Mapped[Song] = relationship("Song", back_populates="analytics", uselist=False)
    most_common_error_type: Mapped[Optional[ErrorType]] = relationship(lazy="joined")

    def __repr__(self) -> str:
        return f"<SongAnalytics song_id={self.song_id}>"

# ---------------------------------------------------------------------------
# End of models file
# ---------------------------------------------------------------------------
