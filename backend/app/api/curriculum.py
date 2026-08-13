from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.curriculum import (
    LearningPath, CurriculumModule, CurriculumUnit, 
    CurriculumLesson, CurriculumExercise, CurriculumCheckpoint
)
from app.models.student_progress import StudentLearningState

router = APIRouter(prefix="/curriculum", tags=["curriculum"])

# --- Pydantic Schemas ---
class ExerciseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    exercise_type: str
    tempo_bpm: int
    key_signature: str
    midi_uri: Optional[str] = None
    display_order: int

class LessonSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    slug: str
    learning_goal: Optional[str] = None
    estimated_time: int
    difficulty: str
    required_skills: List[str] = []
    skills_taught: List[str] = []
    prerequisites: List[str] = []
    xp_reward: int
    ai_coaching_enabled: bool
    teacher_assignable: bool
    display_order: int

class CheckpointSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    pass_threshold_percentage: float
    unlocks_module_id: Optional[UUID] = None

class ModuleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    slug: str
    description: Optional[str] = None
    display_order: int
    is_unlocked_by_default: bool
    checkpoint: Optional[CheckpointSchema] = None

class LearningPathSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    slug: str
    description: Optional[str] = None
    target_role: str
    display_order: int
    modules: List[ModuleSchema] = []

class CheckpointAttemptRequest(BaseModel):
    module_id: UUID
    score_percentage: float

# --- Routes ---

@router.get("/paths", response_model=List[LearningPathSchema])
def list_learning_paths(db: Session = Depends(get_db)):
    """List all published learning paths with their module trees."""
    print("paths endpoint reached")
    return db.query(LearningPath).filter(LearningPath.is_published == True).order_by(LearningPath.display_order.asc()).all()

@router.get("/paths/{path_id_or_slug}", response_model=LearningPathSchema)
def get_learning_path(path_id_or_slug: str, db: Session = Depends(get_db)):
    path = None
    try:
        uuid_val = UUID(path_id_or_slug)
        path = db.query(LearningPath).filter(LearningPath.id == uuid_val).first()
    except ValueError:
        path = db.query(LearningPath).filter(LearningPath.slug == path_id_or_slug).first()

    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    return path

@router.get("/student/state")
def get_student_learning_state(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve or initialize the student's rich learning state."""
    state = db.query(StudentLearningState).filter(StudentLearningState.user_id == current_user.id).first()
    
    if not state:
        # Initialize default state for user
        default_path = db.query(LearningPath).first()
        default_module = db.query(CurriculumModule).filter(CurriculumModule.is_unlocked_by_default == True).first()
        
        state = StudentLearningState(
            user_id=current_user.id,
            current_path_id=default_path.id if default_path else None,
            current_module_id=default_module.id if default_module else None,
            unlocked_module_ids=[str(default_module.id)] if default_module else [],
            unlocked_lesson_ids=[],
            completed_lesson_ids=[],
            skill_levels={"Posture": 85, "Middle C": 90, "Rhythm": 75},
            weak_areas=[{"topic": "Measures 12-16 Rhythm Shift", "severity": "Moderate"}],
            practice_streak_days=1,
            total_xp=150
        )
        db.add(state)
        db.commit()
        db.refresh(state)

    return {
        "user_id": str(state.user_id),
        "current_path_id": str(state.current_path_id) if state.current_path_id else None,
        "current_module_id": str(state.current_module_id) if state.current_module_id else None,
        "unlocked_module_ids": state.unlocked_module_ids or [],
        "unlocked_lesson_ids": state.unlocked_lesson_ids or [],
        "completed_lesson_ids": state.completed_lesson_ids or [],
        "skill_levels": state.skill_levels or {},
        "weak_areas": state.weak_areas or [],
        "practice_streak_days": state.practice_streak_days,
        "total_xp": state.total_xp
    }

@router.post("/student/checkpoint-attempt")
def submit_checkpoint_attempt(
    attempt: CheckpointAttemptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    checkpoint = db.query(CurriculumCheckpoint).filter(CurriculumCheckpoint.module_id == attempt.module_id).first()
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint for module not found")

    passed = attempt.score_percentage >= checkpoint.pass_threshold_percentage
    
    state = db.query(StudentLearningState).filter(StudentLearningState.user_id == current_user.id).first()
    if state and passed and checkpoint.unlocks_module_id:
        unlock_str = str(checkpoint.unlocks_module_id)
        current_unlocked = list(state.unlocked_module_ids or [])
        if unlock_str not in current_unlocked:
            current_unlocked.append(unlock_str)
            state.unlocked_module_ids = current_unlocked
            state.current_module_id = checkpoint.unlocks_module_id
            db.commit()

    return {
        "status": "success",
        "passed": passed,
        "score_percentage": attempt.score_percentage,
        "pass_threshold_percentage": checkpoint.pass_threshold_percentage,
        "unlocked_module_id": str(checkpoint.unlocks_module_id) if (passed and checkpoint.unlocks_module_id) else None
    }
