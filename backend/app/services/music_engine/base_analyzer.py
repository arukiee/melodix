from abc import ABC, abstractmethod
from typing import List, Optional, Dict
import numpy as np
from pydantic import BaseModel, ConfigDict

class PerformanceEvent(BaseModel):
    note: str
    start_time: float
    end_time: float
    duration: float
    confidence: float
    cents_off: float
    dynamic_level: str = "medium"  # "soft" | "medium" | "loud"

class ExpectedEvent(BaseModel):
    note: str
    relative_time: float
    duration: float

class NoteComparisonEvent(BaseModel):
    """Per-note comparison result — one row in the comparison table shown to the student."""
    expected_note: str
    played_note: Optional[str]       # None = missed
    result: str                       # "correct" | "wrong" | "missed" | "extra"
    expected_time: float
    played_time: Optional[float]
    timing_delta_ms: Optional[float]  # positive = late, negative = early
    expected_duration: Optional[float]
    played_duration: Optional[float]
    duration_delta_ms: Optional[float]
    cents_off: Optional[float]

class AnalysisRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    audio_data: np.ndarray
    sample_rate: int
    expected_notes: List[str] = []
    expected_events: List[ExpectedEvent] = []
    target_bpm: int = 60

class AnalysisMistake(BaseModel):
    timestamp: float
    type: str  # "flat" | "sharp" | "wrong_note" | "off_tempo" | "early" | "late" | "missed_note" | "extra_note"
    details: str

class ScoreBreakdown(BaseModel):
    pitchScore: float
    rhythmScore: float
    tempoScore: float
    durationScore: float = 100.0   # NEW — how well note durations matched
    overallScore: float

class TempoMetrics(BaseModel):
    targetBpm: float
    averageBpm: float
    bpmVariance: float
    driftBpm: float
    stabilityScore: float

class AICoachFeedbackSchema(BaseModel):
    summary: str
    strengths: List[str]
    improvements: List[str]
    nextGoal: str

class AnalysisResult(BaseModel):
    version: int = 1
    noteAccuracy: float   # backward compat
    rhythmAccuracy: float
    tempoAccuracy: float
    overallScore: float
    detectedBpm: float
    durationMs: float
    mistakes: List[AnalysisMistake]
    detected_events: List[PerformanceEvent] = []
    scores: ScoreBreakdown
    tempo_metrics: TempoMetrics
    ai_coach_feedback: Optional[AICoachFeedbackSchema] = None
    measure_scores: Dict[int, float] = {}
    measure_dynamics: Dict[int, str] = {}
    # NEW — per-note comparison table
    note_comparison: List[NoteComparisonEvent] = []
    correct_notes: int = 0
    wrong_notes: int = 0
    missed_notes: int = 0
    extra_notes: int = 0

class BaseAudioAnalyzer(ABC):
    @abstractmethod
    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """Runs validation, event extraction, and comparative scoring evaluation."""
        pass
