from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ChordInfo(BaseModel):
    measure: int
    pitches: List[str]
    detected_chord: str


class MissionInfo(BaseModel):
    id: str
    title: str
    type: str
    bpm: int
    learningGoal: str
    xpReward: int
    expectedNotes: List[str] = []


class ImportPreviewResponse(BaseModel):
    title: str
    composer: str
    key_signature: str
    time_signature: str
    bpm: int
    measure_count: int
    note_count: int
    detected_chords: List[ChordInfo]
    generated_missions: List[MissionInfo]
    sections: List[Dict[str, Any]] = []
    steps: List[Dict[str, Any]] = []
    adaptive_thresholds: Dict[str, Any] = {}
    validation_warnings: List[str]
    notes: List[Dict[str, Any]]


class ImportCommitResponse(BaseModel):
    success: bool
    song_id: Optional[str] = None
    message: str
