"""Canonical contracts shared by symbolic and learned piano paths."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class InputMode(str, Enum):
    KEYBOARD = "KEYBOARD"
    MIDI = "MIDI"
    MIC = "MIC"


class MatchStatus(str, Enum):
    CORRECT = "CORRECT"
    EARLY = "EARLY"
    LATE = "LATE"
    MISSED = "MISSED"
    EXTRA = "EXTRA"
    WRONG_PITCH = "WRONG_PITCH"


NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def pitch_name(midi_pitch: int) -> str:
    if not 0 <= midi_pitch <= 127:
        raise ValueError("MIDI pitch must be between 0 and 127")
    return f"{NOTE_NAMES[midi_pitch % 12]}{midi_pitch // 12 - 1}"


@dataclass(frozen=True)
class TargetNote:
    note_id: str
    midi_pitch: int
    start_beat: float
    duration_beats: float
    section_id: str
    hand: str | None = None

    @property
    def pitch_name(self) -> str:
        return pitch_name(self.midi_pitch)


@dataclass(frozen=True)
class PlayedNoteEvent:
    session_id: str
    input_mode: InputMode
    midi_pitch: int
    onset_time_ms: int
    offset_time_ms: int | None = None
    velocity: float = 1.0
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not 0 <= self.midi_pitch <= 127:
            raise ValueError("MIDI pitch must be between 0 and 127")
        if not 0.0 <= self.velocity <= 1.0:
            raise ValueError("velocity must be between 0 and 1")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.offset_time_ms is not None and self.offset_time_ms < self.onset_time_ms:
            raise ValueError("offset_time_ms cannot precede onset_time_ms")

    @property
    def pitch_name(self) -> str:
        return pitch_name(self.midi_pitch)


@dataclass(frozen=True)
class NoteMatch:
    played_index: int | None
    target_note_id: str | None
    status: MatchStatus
    timing_error_ms: float | None = None
    midi_pitch: int | None = None
    section_id: str | None = None


@dataclass
class ScoreResult:
    pitch_accuracy: float
    timing_accuracy: float
    completion_score: float
    extra_note_rate: float
    tempo_stability: float
    overall_score: float
    matches: list[NoteMatch] = field(default_factory=list)
    section_scores: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "pitch_accuracy": self.pitch_accuracy,
            "timing_accuracy": self.timing_accuracy,
            "completion_score": self.completion_score,
            "extra_note_rate": self.extra_note_rate,
            "tempo_stability": self.tempo_stability,
            "overall_score": self.overall_score,
            "section_scores": self.section_scores,
        }
