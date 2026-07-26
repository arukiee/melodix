# backend/app/repositories/song_difficulty.py
"""Repository for the SongDifficulty one-to-one entity.
Provides CRUD operations and any convenience helpers.
All methods return raw SQLAlchemy model instances.
"""

from __future__ import annotations

from typing import Any, Dict, Sequence

from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.songs import SongDifficulty


class SongDifficultyRepository(BaseRepository[SongDifficulty]):
    """Concrete repository for :class:`backend.app.models.songs.SongDifficulty`."""

    model = SongDifficulty

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    # Generic BaseRepository methods already cover create, update, get_by_id, etc.
    # Additional domain‑specific helpers can be added here if needed.
