# backend/app/api/songs.py
"""Songs REST API router.
Thin endpoints that delegate to the service layer via dependency‑injection
factory functions defined in ``app.services.dependencies``.
All responses use Pydantic v2 ``model_validate`` to convert ORM models to
schema objects.
"""

from fastapi import APIRouter, Depends, status
from typing import Optional

from app.services.dependencies import get_song_service
from app.services.song import SongService

from app.schemas.song import SongCreate, SongUpdate, SongDetail, SongSummary
from app.schemas.song_difficulty import SongDifficultyDetail
from app.schemas.song_technique import SongTechniqueDetail
from app.schemas.song_skill import SkillDetail

router = APIRouter(prefix="/songs", tags=["songs"])

# ---------------------------------------------------------------------
# CRUD endpoints
# ---------------------------------------------------------------------
@router.post("/", response_model=SongDetail, status_code=status.HTTP_201_CREATED)
def create_song(
    song_in: SongCreate,
    service: SongService = Depends(get_song_service),
):
    """Create a new song.
    ``SongCreate`` contains only user‑provided fields; the service returns the
    freshly persisted SQLAlchemy model which is then transformed to the
    ``SongDetail`` response schema.
    """
    song = service.create_song(song_in.model_dump())
    return SongDetail.model_validate(song)


@router.get("/{song_id}", response_model=SongDetail)
def read_song(
    song_id: int,
    service: SongService = Depends(get_song_service),
):
    """Retrieve a song by its primary key."""
    song = service.get_song(song_id)
    return SongDetail.model_validate(song)


@router.patch("/{song_id}", response_model=SongDetail)
def update_song(
    song_id: int,
    song_in: SongUpdate,
    service: SongService = Depends(get_song_service),
):
    """Partially update a song (PATCH semantics)."""
    song = service.update_song(song_id, song_in.model_dump(exclude_unset=True))
    return SongDetail.model_validate(song)


@router.delete("/{song_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_song(
    song_id: int,
    service: SongService = Depends(get_song_service),
):
    """Soft‑delete (archive) a song. Returns no content."""
    service.archive_song(song_id)
    return None

# ---------------------------------------------------------------------
# Publication helpers
# ---------------------------------------------------------------------
@router.post("/{song_id}/publish", response_model=SongDetail)
def publish_song(
    song_id: int,
    service: SongService = Depends(get_song_service),
):
    song = service.publish_song(song_id)
    return SongDetail.model_validate(song)


@router.post("/{song_id}/unpublish", response_model=SongDetail)
def unpublish_song(
    song_id: int,
    service: SongService = Depends(get_song_service),
):
    song = service.unpublish_song(song_id)
    return SongDetail.model_validate(song)

# ---------------------------------------------------------------------
# Difficulty endpoint
# ---------------------------------------------------------------------
@router.put("/{song_id}/difficulty", response_model=SongDifficultyDetail)
def set_difficulty(
    song_id: int,
    level: int,
    notes: Optional[str] = None,
    service: SongService = Depends(get_song_service),
):
    diff = service.set_difficulty(song_id, level, notes)
    return diff

# ---------------------------------------------------------------------
# Technique & Skill synchronization
# ---------------------------------------------------------------------
@router.put("/{song_id}/techniques", response_model=list[SongTechniqueDetail])
def replace_techniques(
    song_id: int,
    technique_ids: list[int],
    service: SongService = Depends(get_song_service),
):
    return service.replace_techniques(song_id, technique_ids)


@router.put("/{song_id}/skills", response_model=list[SkillDetail])
def replace_skills(
    song_id: int,
    skill_ids: list[int],
    service: SongService = Depends(get_song_service),
):
    return service.replace_skills(song_id, skill_ids)
