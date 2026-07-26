# backend/app/repositories/song.py
"""Repository for the Song aggregate.
Provides CRUD, pagination, soft‑delete, and eager loading of related entities.
All methods return raw SQLAlchemy model instances.
"""

from __future__ import annotations

from typing import Any, Dict, Sequence

from sqlalchemy.orm import Session, selectinload

from .base import BaseRepository
from ..models.songs import Song


class SongRepository(BaseRepository[Song]):
    """Concrete repository for :class:`backend.app.models.songs.Song`."""

    model = Song

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    # ---------------------------------------------------------------------
    # Listing with eager loading of relationships
    # ---------------------------------------------------------------------
    def list(
        self,
        *,
        filters: Dict[str, Any] | None = None,
        offset: int = 0,
        limit: int = 100,
        order_by: Any | None = None,
        include_deleted: bool = False,
    ) -> Sequence[Song]:
        """Return a list of :class:`Song` objects with common relationships loaded.

        ``filters`` is a mapping of column names to exact values; more advanced
        filtering is performed via the shared ``apply_song_filters`` helper (see
        ``filters.py``).
        """
        query = self.session.query(self.model)
        if not include_deleted and hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        if filters:
            query = query.filter_by(**filters)
        # eager‑load collections that are frequently accessed
        query = query.options(
            selectinload(self.model.files),
            selectinload(self.model.difficulty),
            selectinload(self.model.techniques),
            selectinload(self.model.skills),
            selectinload(self.model.events),
            selectinload(self.model.ground_truth_meta),
            selectinload(self.model.analytics),
        )
        if order_by is not None:
            query = query.order_by(order_by)
        return query.offset(offset).limit(limit).all()

    # ---------------------------------------------------------------------
    # Soft‑delete (archive) and restore helpers
    # ---------------------------------------------------------------------
    def archive(self, song: Song) -> Song:
        """Soft‑delete a song (set ``deleted_at``)."""
        return self.delete(song, soft=True)

    def restore(self, song: Song) -> Song:
        """Restore a soft‑deleted song by clearing ``deleted_at``."""
        if hasattr(song, "deleted_at"):
            song.deleted_at = None
            self.session.flush()
        return song

    # ---------------------------------------------------------------------
    # Publication helpers
    # ---------------------------------------------------------------------
    def publish(self, song: Song, published_at) -> Song:
        song.is_public = True
        song.published_at = published_at
        self.session.flush()
        return song

    def unpublish(self, song: Song) -> Song:
        song.is_public = False
        song.published_at = None
        self.session.flush()
        return song
