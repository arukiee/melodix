"""Pydantic schemas for the audio upload and processing pipeline."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


# ─────────────────────────────────────────────────────────────────────────────
# Audio Asset schemas
# ─────────────────────────────────────────────────────────────────────────────

class AudioUploadResponse(BaseModel):
    """Returned after a successful audio upload."""
    model_config = ConfigDict(from_attributes=True)

    audio_asset_id: UUID
    processing_job_id: UUID
    original_filename: str
    file_hash_sha256: str
    file_size_bytes: int
    format: str
    message: str = "Upload successful. Processing started."


class AudioAssetSchema(BaseModel):
    """Full audio asset representation."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    song_id: Optional[UUID] = None
    source_type: str
    original_filename: str
    file_hash_sha256: str
    format: str
    duration_seconds: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    file_size_bytes: int
    is_valid: bool = False
    validation_errors: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[datetime] = None


# ─────────────────────────────────────────────────────────────────────────────
# Processing Job schemas
# ─────────────────────────────────────────────────────────────────────────────

class ProcessingJobStatus(BaseModel):
    """Pipeline status response — what the frontend polls."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    audio_asset_id: UUID
    song_id: Optional[UUID] = None
    status: str              # ProcessingJobStage value
    progress_percent: int = 0
    pipeline_version: str = "1.0.0"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    stage_log: List[Dict[str, Any]] = []
    created_at: Optional[datetime] = None

    # Populated once completed
    transcription_id: Optional[UUID] = None
    note_count: Optional[int] = None
    tempo_bpm: Optional[float] = None
    tempo_confidence: Optional[float] = None


class ProcessingJobSummary(BaseModel):
    """Compact version for list views."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    progress_percent: int = 0
    pipeline_version: str
    created_at: Optional[datetime] = None


# ─────────────────────────────────────────────────────────────────────────────
# Transcription schemas
# ─────────────────────────────────────────────────────────────────────────────

class TranscriptionSchema(BaseModel):
    """Transcription result summary."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    processing_job_id: UUID
    audio_asset_id: UUID
    song_id: Optional[UUID] = None
    model_name: str = "basic-pitch"
    model_version: str
    note_count: int = 0
    duration_seconds: Optional[float] = None
    processing_time_ms: Optional[int] = None
    created_at: Optional[datetime] = None


class CanonicalNote(BaseModel):
    """
    A single note in Melodix canonical format.
    Every field traces back to actual processing — no invented data.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    sequence_index: int
    midi_number: int = Field(ge=0, le=127, description="MIDI note number")
    note_name: str = Field(description="e.g. 'C4', 'E4'")
    start_time: float = Field(description="Start time in seconds")
    end_time: float = Field(description="End time in seconds")
    duration: float = Field(description="Duration in seconds")
    velocity: int = Field(ge=0, le=127, default=80)
    confidence: float = Field(
        ge=0.0, le=1.0, default=0.0,
        description="Melodix-computed confidence from model activation data"
    )
    is_validated: bool = False
    validation_action: Optional[str] = None
    hand: str = "UNASSIGNED"
    measure_number: Optional[int] = None
    beat_position: Optional[float] = None


class TranscriptionNotesResponse(BaseModel):
    """Response containing all notes from a transcription."""
    transcription_id: UUID
    model_name: str
    model_version: str
    note_count: int
    notes: List[CanonicalNote]


# ─────────────────────────────────────────────────────────────────────────────
# Difficulty schemas
# ─────────────────────────────────────────────────────────────────────────────

class DifficultyMetricsSchema(BaseModel):
    """Computed difficulty features — every value from actual analysis."""
    notes_per_second: float = 0.0
    polyphony_ratio: float = 0.0
    chord_density: float = 0.0
    avg_hand_jump_semitones: float = 0.0
    max_hand_jump_semitones: int = 0
    tempo_bpm: float = 0.0
    syncopation_ratio: float = 0.0
    pitch_range_semitones: int = 0
    max_simultaneous_notes: int = 0


class DifficultyVariantSchema(BaseModel):
    """A difficulty variant of a transcription."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    transcription_id: UUID
    song_id: Optional[UUID] = None
    level: str               # EASY, MEDIUM, HARD, EXPERT
    metrics: DifficultyMetricsSchema
    difficulty_score: float = 0.0
    note_count: int = 0
    tempo_multiplier: float = 1.0
    hands_used: str = "BOTH"
    engine_version: str = "1.0.0"
    created_at: Optional[datetime] = None


class DifficultyNoteSchema(BaseModel):
    """A note within a difficulty variant, linked to its source transcription note."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_note_id: int      # provenance: FK to TranscriptionNote
    sequence_index: int
    midi_number: int
    note_name: str
    start_time: float
    end_time: float
    duration: float
    velocity: int
    hand: str
    measure_number: Optional[int] = None
    beat_position: Optional[float] = None
    importance_score: float = 0.5


class DifficultyVariantDetailResponse(BaseModel):
    """Full difficulty variant with all notes."""
    variant: DifficultyVariantSchema
    notes: List[DifficultyNoteSchema]


# ─────────────────────────────────────────────────────────────────────────────
# BPM Analysis schemas
# ─────────────────────────────────────────────────────────────────────────────

class BPMAnalysisResult(BaseModel):
    """
    BPM detection result.
    confidence is MELODIX-COMPUTED from beat interval consistency,
    onset alignment, and tempo stability — NOT from librosa.
    """
    tempo_bpm: float
    beat_times: List[float]
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Melodix-computed confidence (NOT from librosa)"
    )
    time_signature: str = "4/4"
    method: str = "librosa_beat_track"
    engine_version: str = "1.0.0"


# ─────────────────────────────────────────────────────────────────────────────
# Provenance schema
# ─────────────────────────────────────────────────────────────────────────────

class ProvenanceSchema(BaseModel):
    """
    Full provenance chain for any processed song.
    Answers: 'Where did this C4 come from?'
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    processing_job_id: UUID
    song_id: Optional[UUID] = None
    audio_asset_id: UUID
    transcription_id: Optional[UUID] = None
    pipeline_version: str
    source_type: str
    file_hash: str
    audio_duration: Optional[float] = None
    transcription_model: Optional[str] = None
    transcription_model_version: Optional[str] = None
    bpm_engine_version: Optional[str] = None
    difficulty_engine_version: Optional[str] = None
    tempo_value: Optional[float] = None
    tempo_confidence: Optional[float] = None
    note_count: Optional[int] = None
    difficulty_variants_summary: Dict[str, int] = {}
    artifact_paths: Dict[str, str] = {}
    created_at: Optional[datetime] = None


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline artifacts schema
# ─────────────────────────────────────────────────────────────────────────────

class PipelineArtifactsResponse(BaseModel):
    """Lists all MinIO artifacts for a processing job."""
    processing_job_id: UUID
    audio_artifacts: Dict[str, str] = {}     # {original: path, metadata: path}
    transcription_artifacts: Dict[str, str] = {}  # {raw_midi: path, note_events: path, model_output: path}
    analysis_artifacts: Dict[str, str] = {}  # {bpm: path, chords: path, validation: path, difficulty: path}
