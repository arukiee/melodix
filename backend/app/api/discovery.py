from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.discovery import Classroom
from app.models.user import User
from app.schemas.song import ClassroomSchema, DiscoveryHomeResponse, SemanticSearchResponse
from app.services.discovery.recommend import build_home_rows
from app.services.discovery.semantic import semantic_search, index_missing_embeddings
from app.services.discovery.serialize import saved_song_ids

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.get("/home", response_model=DiscoveryHomeResponse)
def discovery_home(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ids = saved_song_ids(db, current_user.id)
    return build_home_rows(db, current_user, saved_ids=ids)


@router.get("/semantic", response_model=SemanticSearchResponse)
async def discovery_semantic(
    q: str = Query(..., min_length=2, description="Natural language song search"),
    limit: int = Query(12, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ids = saved_song_ids(db, current_user.id)
    return await semantic_search(db, q, saved_ids=ids, limit=limit)


@router.post("/index-embeddings")
async def reindex_embeddings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = await index_missing_embeddings(db)
    return {"indexed": count, "user": str(current_user.id)}


@router.get("/classes", response_model=list[ClassroomSchema])
def list_teacher_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    classes = db.query(Classroom).filter(Classroom.teacher_id == current_user.id).order_by(Classroom.name.asc()).all()
    return classes
