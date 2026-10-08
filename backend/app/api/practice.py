import uuid
from uuid import UUID
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.music_engine.practice_scorer import (
    score_segment,
    build_session_summary,
)
from app.services.music_engine.practice_session_service import (
    complete_job_mission,
    record_job_score,
    start_job_session,
    complete_song_mission,
    record_song_score,
    start_song_session,
)

router = APIRouter(prefix="/practice", tags=["practice"])

# --- Schemas ---
class PracticeSessionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    lesson_id: str
    overall_progress: float
    phases: List[Dict[str, Any]] = []
    levels: List[Dict[str, Any]] = []
    lyricAlignment: Optional[Dict[str, Any]] = None
    phrases: List[Dict[str, Any]] = []
    processing_job_id: Optional[str] = None
    song_id: Optional[str] = None
    current_mission_id: Optional[str] = None
    current_level_id: Optional[str] = None
    completed_mission_ids: List[str] = []
    mission_scores: Dict[str, Any] = {}
    attempts: Dict[str, Any] = {}

class MissionUpdatePayload(BaseModel):
    status: str
    score: Optional[float] = None


# ---------------------------------------------------------------------------
# /practice/score  — per-segment scoring schemas
# ---------------------------------------------------------------------------

class StudentNoteEvent(BaseModel):
    """One note event as output by the CNN-BiLSTM / Transcriber."""
    note: str                     # e.g. "A4"
    onset: float                  # seconds from start of the buffered chunk
    velocity: int = 64            # MIDI velocity 0-127
    duration: Optional[float] = None


class ScoreRequest(BaseModel):
    """
    Body sent by the client after transcribing or recording play.
    """
    segment_id: str
    processing_job_id: Optional[UUID] = None
    song_id: Optional[UUID] = None
    mission_id: Optional[str] = None
    student_notes: List[StudentNoteEvent]
    reference_notes: List[StudentNoteEvent]   # echoed from phrase expectedEvents
    prior_segment_scores: Optional[List[Dict[str, Any]]] = None


class NoteErrorTag(BaseModel):
    position: int
    ref_note: Optional[str]
    stu_note: Optional[str]
    tags: List[str]


class SegmentScoreResponse(BaseModel):
    segment_id: str
    accuracy_score: float           # 0.0 – 1.0
    expressiveness_score: float     # 0.0 – 5.0
    error_tags: List[NoteErrorTag]


class SessionSummary(BaseModel):
    overall_accuracy: float
    overall_expressiveness: float
    segments_scored: int


class ScoreResponse(BaseModel):
    segment: SegmentScoreResponse
    session_summary: Optional[SessionSummary] = None

# --- Catalog / Seeded song practice endpoints ---
@router.get("/songs/{song_id}", response_model=PracticeSessionResponse)
def get_song_practice(
    song_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start or resume practice for a hand-authored or seeded catalog song."""
    try:
        return start_song_session(db, current_user.id, song_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/songs/{song_id}/missions/{mission_id}", response_model=PracticeSessionResponse)
def update_song_mission(
    song_id: UUID,
    mission_id: str,
    payload: MissionUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Advance mission status and store scores for a song practice session."""
    if payload.status not in {"completed", "in_progress"}:
        raise HTTPException(status_code=400, detail="Only completed or in_progress mission updates are supported")
    if payload.status == "in_progress":
        return get_song_practice(song_id, db, current_user)
    try:
        return complete_song_mission(db, current_user.id, song_id, mission_id, payload.score)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# --- Generated-song practice endpoints ---
@router.get("/jobs/{job_id}", response_model=PracticeSessionResponse)
def get_job_practice(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start or resume practice for the curriculum created from this job."""
    try:
        return start_job_session(db, current_user.id, job_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/jobs/{job_id}/missions/{mission_id}", response_model=PracticeSessionResponse)
def update_job_mission(
    job_id: UUID,
    mission_id: str,
    payload: MissionUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.status not in {"completed", "in_progress"}:
        raise HTTPException(status_code=400, detail="Only completed or in_progress mission updates are supported")
    if payload.status == "in_progress":
        return get_job_practice(job_id, db, current_user)
    try:
        return complete_job_mission(db, current_user.id, job_id, mission_id, payload.score)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# POST /practice/score
# ---------------------------------------------------------------------------

@router.post("/score", response_model=ScoreResponse)
def score_practice_segment(
    payload: ScoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScoreResponse:
    """
    Score one buffered segment of student play against its reference phrase.
    """
    student_dicts   = [n.model_dump() for n in payload.student_notes]
    reference_dicts = [n.model_dump() for n in payload.reference_notes]

    seg_score = score_segment(
        segment_id     = payload.segment_id,
        student_notes  = student_dicts,
        reference_notes= reference_dicts,
    )

    session_summary_obj = None
    if payload.prior_segment_scores is not None:
        from app.services.music_engine.practice_scorer import SegmentScore
        prior = [
            SegmentScore(
                segment_id=s["segment_id"],
                accuracy_score=s["accuracy_score"],
                expressiveness_score=s["expressiveness_score"],
                error_tags=s["error_tags"],
            )
            for s in payload.prior_segment_scores
        ]
        all_scores = prior + [seg_score]
        summary = build_session_summary(all_scores)
        session_summary_obj = SessionSummary(**summary)

    target_id = payload.song_id or payload.processing_job_id
    if target_id and payload.mission_id:
        tags = [tag for error in seg_score.error_tags for tag in error["tags"]]
        total = max(1, len(seg_score.error_tags))
        pitch_accuracy = 1.0 - (tags.count("pitch_error") / total)
        timing_accuracy = 1.0 - (tags.count("timing_error") / total)
        try:
            if payload.song_id:
                record_song_score(
                    db,
                    current_user.id,
                    payload.song_id,
                    payload.mission_id,
                    pitch_accuracy,
                    timing_accuracy,
                    seg_score.accuracy_score,
                )
            else:
                record_job_score(
                    db,
                    current_user.id,
                    payload.processing_job_id,
                    payload.mission_id,
                    pitch_accuracy,
                    timing_accuracy,
                    seg_score.accuracy_score,
                )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    return ScoreResponse(
        segment=SegmentScoreResponse(
            segment_id           = seg_score.segment_id,
            accuracy_score       = seg_score.accuracy_score,
            expressiveness_score = seg_score.expressiveness_score,
            error_tags           = [
                NoteErrorTag(**t) for t in seg_score.error_tags
            ],
        ),
        session_summary=session_summary_obj,
    )
