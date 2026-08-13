from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, case
from typing import Optional, List
import uuid
import re
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.lesson import Lesson as LessonModel
from app.models.lesson_progress import LessonProgress as LessonProgressModel
from app.schemas.lesson import (
    LessonCreate, LessonUpdate, LessonResponse, LessonListResponse,
    LessonProgressUpdate, LessonProgressResponse
)

router = APIRouter(prefix="/lessons", tags=["lessons"])

def slugify(title: str) -> str:
    # Basic slugification helper
    s = title.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    return s

def generate_unique_slug(title: str, db: Session) -> str:
    base_slug = slugify(title)
    if not base_slug:
        base_slug = "lesson"
    
    slug = base_slug
    counter = 1
    while db.query(LessonModel).filter(LessonModel.slug == slug, LessonModel.is_deleted == False).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug

@router.get("", response_model=LessonListResponse)
def list_lessons(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("newest", pattern="^(newest|oldest|difficulty|duration)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    # Query building
    query = db.query(LessonModel).filter(LessonModel.is_deleted == False)

    # Permission check: Students only see published lessons
    if current_user.role == "STUDENT":
        query = query.filter(LessonModel.is_published == True)
    
    # Filtering
    if category:
        query = query.filter(LessonModel.category.ilike(category))
    if difficulty:
        query = query.filter(LessonModel.difficulty == difficulty.upper())
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                LessonModel.title.ilike(search_filter),
                LessonModel.description.ilike(search_filter),
                LessonModel.category.ilike(search_filter),
                LessonModel.genre.ilike(search_filter)
            )
        )
    
    # Sorting
    if sort_by == "newest":
        query = query.order_by(LessonModel.created_at.desc())
    elif sort_by == "oldest":
        query = query.order_by(LessonModel.created_at.asc())
    elif sort_by == "difficulty":
        # Custom ordering for difficulty: BEGINNER, INTERMEDIATE, ADVANCED
        query = query.order_by(
            case(
                (LessonModel.difficulty == "BEGINNER", 1),
                (LessonModel.difficulty == "INTERMEDIATE", 2),
                (LessonModel.difficulty == "ADVANCED", 3),
                else_=4
            )
        )
    elif sort_by == "duration":
        query = query.order_by(LessonModel.estimated_duration.asc())

    # Pagination
    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    # Hydrate songs count and format response
    response_items = []
    for item in items:
        songs_count = len(item.songs) if item.songs else 0
        resp = LessonResponse.model_validate(item)
        resp.songs_count = songs_count
        response_items.append(resp)

    return {
        "items": response_items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{id_or_slug}", response_model=LessonResponse)
def get_lesson(
    id_or_slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Try finding by UUID first, then slug
    lesson = None
    try:
        uuid_val = uuid.UUID(id_or_slug)
        lesson = db.query(LessonModel).filter(LessonModel.id == uuid_val, LessonModel.is_deleted == False).first()
    except ValueError:
        lesson = db.query(LessonModel).filter(LessonModel.slug == id_or_slug, LessonModel.is_deleted == False).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Authorization Check
    if current_user.role == "STUDENT" and not lesson.is_published:
        raise HTTPException(status_code=403, detail="Not authorized to access this lesson")

    # Hydrate response
    songs_count = len(lesson.songs) if lesson.songs else 0
    resp = LessonResponse.model_validate(lesson)
    resp.songs_count = songs_count
    return resp

@router.post("", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
def create_lesson(
    lesson_in: LessonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):


    # Generate slug if not provided
    slug = lesson_in.slug if lesson_in.slug else generate_unique_slug(lesson_in.title, db)
    
    # Ensure slug uniqueness
    existing = db.query(LessonModel).filter(LessonModel.slug == slug, LessonModel.is_deleted == False).first()
    if existing:
        slug = generate_unique_slug(lesson_in.title, db)

    new_lesson = LessonModel(
        teacher_id=current_user.id,
        title=lesson_in.title,
        slug=slug,
        description=lesson_in.description,
        category=lesson_in.category,
        difficulty=lesson_in.difficulty,
        genre=lesson_in.genre,
        estimated_duration=lesson_in.estimated_duration,
        display_order=lesson_in.display_order,
        thumbnail_url=lesson_in.thumbnail_url,
        objectives=[obj.model_dump() for obj in lesson_in.objectives],
        steps=[step.model_dump() for step in lesson_in.steps] if lesson_in.steps else [],
        adaptive_thresholds=lesson_in.adaptive_thresholds or {},
        visibility=lesson_in.visibility,
        is_published=lesson_in.is_published,
        published_at=datetime.utcnow() if lesson_in.is_published else None
    )

    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)
    
    resp = LessonResponse.model_validate(new_lesson)
    resp.songs_count = 0
    return resp

@router.patch("/{id}", response_model=LessonResponse)
def update_lesson(
    id: uuid.UUID,
    updates: LessonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lesson = db.query(LessonModel).filter(LessonModel.id == id, LessonModel.is_deleted == False).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Permission check: must be owner teacher or admin
    if current_user.role != "ADMIN" and lesson.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this lesson")

    update_data = updates.model_dump(exclude_unset=True)

    # Specific logic for toggling publish state / published_at
    if "is_published" in update_data:
        if update_data["is_published"] and not lesson.is_published:
            lesson.published_at = datetime.utcnow()
        elif not update_data["is_published"]:
            lesson.published_at = None

    if "objectives" in update_data and update_data["objectives"] is not None:
        lesson.objectives = [obj.model_dump() for obj in update_data["objectives"]]
        del update_data["objectives"]
        
    if "steps" in update_data and update_data["steps"] is not None:
        lesson.steps = [step.model_dump() for step in update_data["steps"]]
        del update_data["steps"]

    for field, value in update_data.items():
        setattr(lesson, field, value)

    db.commit()
    db.refresh(lesson)

    songs_count = len(lesson.songs) if lesson.songs else 0
    resp = LessonResponse.model_validate(lesson)
    resp.songs_count = songs_count
    return resp

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lesson = db.query(LessonModel).filter(LessonModel.id == id, LessonModel.is_deleted == False).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Permission check
    if current_user.role != "ADMIN" and lesson.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this lesson")

    # Soft Delete
    lesson.is_deleted = True
    lesson.deleted_at = datetime.utcnow()
    db.commit()

@router.get("/teachers/me/lessons", response_model=LessonListResponse)
def list_teacher_lessons(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    if current_user.role not in ["TEACHER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Only teachers and admins can view teacher dashboard lessons")

    query = db.query(LessonModel).filter(LessonModel.teacher_id == current_user.id, LessonModel.is_deleted == False)
    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    response_items = []
    for item in items:
        songs_count = len(item.songs) if item.songs else 0
        resp = LessonResponse.model_validate(item)
        resp.songs_count = songs_count
        response_items.append(resp)

    return {
        "items": response_items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

# --- Lesson Progress Endpoints ---

@router.post("/{lesson_id}/progress", response_model=LessonProgressResponse)
def update_lesson_progress(
    lesson_id: uuid.UUID,
    progress_in: LessonProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lesson = db.query(LessonModel).filter(LessonModel.id == lesson_id, LessonModel.is_deleted == False).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Find existing or create new progress record
    progress = db.query(LessonProgressModel).filter(
        LessonProgressModel.user_id == current_user.id,
        LessonProgressModel.lesson_id == lesson_id
    ).first()

    now = datetime.utcnow()
    completed = progress_in.progress_percentage >= 100.0

    if not progress:
        progress = LessonProgressModel(
            user_id=current_user.id,
            lesson_id=lesson_id,
            progress_percentage=progress_in.progress_percentage,
            completed=completed,
            last_opened=now,
            completed_at=now if completed else None
        )
        db.add(progress)
    else:
        progress.progress_percentage = progress_in.progress_percentage
        progress.last_opened = now
        if completed and not progress.completed:
            progress.completed = True
            progress.completed_at = now
        elif not completed:
            progress.completed = False
            progress.completed_at = None

    db.commit()
    db.refresh(progress)
    return progress

from pydantic import BaseModel as PydanticBaseModel

class PracticeSessionLog(PydanticBaseModel):
    song_id: Optional[str] = None
    duration_seconds: int = 180
    accuracy: float = 90.0
    rhythm_score: float = 85.0
    xp_gained: int = 150

@router.post("/practice/session")
def log_practice_session(
    session_in: PracticeSessionLog,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = current_user.profile
    if profile:
        # Increment total daily practice time in minutes if recorded
        added_minutes = max(1, session_in.duration_seconds // 60)
        db.commit()

    return {
        "status": "success",
        "user_id": str(current_user.id),
        "duration_seconds": session_in.duration_seconds,
        "accuracy": session_in.accuracy,
        "rhythm_score": session_in.rhythm_score,
        "xp_gained": session_in.xp_gained,
        "timestamp": datetime.utcnow().isoformat()
    }

