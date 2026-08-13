import uuid
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.lesson_progress import LessonProgress
from app.models.student_progress import StudentLearningState

router = APIRouter(prefix="/practice", tags=["practice"])

# --- Schemas ---
class MissionState(BaseModel):
    id: str
    title: str
    type: str
    bpm: Optional[int] = None
    status: str  # locked, available, in_progress, completed
    progress: float
    learningGoal: Optional[str] = None
    xpReward: Optional[int] = None

class PracticePhaseState(BaseModel):
    id: str
    title: str
    missions: List[MissionState]

class PracticeSessionResponse(BaseModel):
    lesson_id: str
    overall_progress: float
    phases: List[PracticePhaseState]

class MissionUpdatePayload(BaseModel):
    status: str
    score: Optional[float] = None

# --- Helper to build dynamic practice stages based on User state ---
def get_or_create_practice_session(db: Session, user_id: uuid.UUID, lesson_id: uuid.UUID) -> PracticeSessionResponse:
    # 1. Retrieve or initialize LessonProgress
    progress = db.query(LessonProgress).filter(
        LessonProgress.user_id == user_id,
        LessonProgress.lesson_id == lesson_id
    ).first()

    if not progress:
        progress = LessonProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            progress_percentage=0.0,
            completed=False,
            last_opened=datetime.utcnow()
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)

    # Fetch student learning state to read unlocked/completed items if needed
    state = db.query(StudentLearningState).filter(StudentLearningState.user_id == user_id).first()
    completed_missions = []
    
    # Simple rule-based serialization of the practice path
    # Twinkle/Ode sequence of missions
    raw_missions = [
        # Phase 1
        ("phase-1", "Phase 1 — Familiarization", "m-listen", "Listen & Watch", "listen", None, 50, "Listen to the recording and watch key orientation."),
        # Phase 2
        ("phase-2", "Phase 2 — Right Hand Foundations", "m-rh-notes", "Right Hand Notes", "right_hand", None, 100, "Practice right-hand notes at slow tempo."),
        ("phase-2", "Phase 2 — Right Hand Foundations", "m-rh-rhythm", "Right Hand Rhythm", "right_hand", None, 100, "Perfect right-hand rhythm with metronome."),
        # Phase 3
        ("phase-3", "Phase 3 — Left Hand Foundations", "m-lh-notes", "Left Hand Notes", "left_hand", None, 100, "Practice left-hand chord/bass accompaniment."),
        ("phase-3", "Phase 3 — Left Hand Foundations", "m-lh-rhythm", "Left Hand Rhythm", "left_hand", None, 100, "Practice left-hand accompaniment rhythm."),
        # Phase 4
        ("phase-4", "Phase 4 — Coordination & Tempo", "m-both-slow", "Hands Together Slowly", "both_hands", 40, 150, "Play slowly with both hands coordinated."),
        ("phase-4", "Phase 4 — Coordination & Tempo", "m-both-med", "Medium Tempo Practice", "tempo", 60, 150, "Increase coordination speed smoothly."),
        ("phase-4", "Phase 4 — Coordination & Tempo", "m-both-full", "Original Tempo", "tempo", 80, 200, "Play at original tempo without stopping."),
        # Phase 5
        ("phase-5", "Phase 5 — Performance Recital", "m-performance", "AI Performance Evaluation", "performance", None, 300, "Complete comprehensive AI note and tempo recital.")
    ]

    # Decide status mapping based on progress_percentage
    # For simplicity, progress_percentage translates to completing a specific count of missions
    # Total missions = 9. Each mission represents ~11.11% progress.
    total_missions_count = len(raw_missions)
    completed_count = int((progress.progress_percentage / 100.0) * total_missions_count)
    completed_count = min(completed_count, total_missions_count)

    phases_map = {}
    for index, (phase_id, phase_title, m_id, m_title, m_type, bpm, xp, goal) in enumerate(raw_missions):
        if phase_id not in phases_map:
            phases_map[phase_id] = {
                "id": phase_id,
                "title": phase_title,
                "missions": []
            }

        # Status rules:
        if index < completed_count:
            status_str = "completed"
            m_progress = 100.0
        elif index == completed_count:
            status_str = "available"
            m_progress = 0.0
        else:
            status_str = "locked"
            m_progress = 0.0

        phases_map[phase_id]["missions"].append(
            MissionState(
                id=m_id,
                title=m_title,
                type=m_type,
                bpm=bpm,
                status=status_str,
                progress=m_progress,
                learningGoal=goal,
                xpReward=xp
            )
        )

    return PracticeSessionResponse(
        lesson_id=str(lesson_id),
        overall_progress=progress.progress_percentage,
        phases=[PracticePhaseState(**v) for v in phases_map.values()]
    )

# --- Endpoints ---
@router.get("/lessons/{lesson_id}", response_model=PracticeSessionResponse)
def get_lesson_practice(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve or initialize the structured practice session for a lesson."""
    return get_or_create_practice_session(db, current_user.id, lesson_id)

@router.patch("/lessons/{lesson_id}/missions/{mission_id}", response_model=PracticeSessionResponse)
def update_mission_progress(
    lesson_id: UUID,
    mission_id: str,
    payload: MissionUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marks a mission completed, updates DB states, and returns the next practice state."""
    progress = db.query(LessonProgress).filter(
        LessonProgress.user_id == current_user.id,
        LessonProgress.lesson_id == lesson_id
    ).first()

    if not progress:
        raise HTTPException(status_code=404, detail="Lesson progress session not found")

    raw_missions = ["m-listen", "m-rh-notes", "m-rh-rhythm", "m-lh-notes", "m-lh-rhythm", "m-both-slow", "m-both-med", "m-both-full", "m-performance"]
    if mission_id not in raw_missions:
        raise HTTPException(status_code=400, detail="Invalid mission ID")

    mission_idx = raw_missions.index(mission_id)
    total_missions_count = len(raw_missions)
    
    current_completed_count = int((progress.progress_percentage / 100.0) * total_missions_count)

    # Progression logic: Only advance progress if the completed mission is the current available one
    if payload.status == "completed" and mission_idx == current_completed_count:
        new_completed_count = current_completed_count + 1
        new_percentage = min(100.0, (new_completed_count / total_missions_count) * 100.0)
        progress.progress_percentage = new_percentage
        progress.last_opened = datetime.utcnow()
        if new_percentage >= 100.0:
            progress.completed = True
            progress.completed_at = datetime.utcnow()

            # Add to student completed lesson list
            state = db.query(StudentLearningState).filter(StudentLearningState.user_id == current_user.id).first()
            if state:
                completed_list = list(state.completed_lesson_ids or [])
                lesson_str = str(lesson_id)
                if lesson_str not in completed_list:
                    completed_list.append(lesson_str)
                    state.completed_lesson_ids = completed_list

        db.commit()
        db.refresh(progress)

    return get_or_create_practice_session(db, current_user.id, lesson_id)
