# backend/app/repositories/song_file.py
"""Repository for the SongFile aggregate.
Handles CRUD, version bumping, primary‑file enforcement and bulk event ingestion.
All methods return raw SQLAlchemy model instances.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from .base import BaseRepository
from ..models.songs import SongFile, FileTypeEnum


class SongFileRepository(BaseRepository[SongFile]):
    """Concrete repository for :class:`backend.app.models.songs.SongFile`."""

    model = SongFile

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    # ---------------------------------------------------------------------
    # Primary‑file helpers
    # ---------------------------------------------------------------------
    def get_primary(self, song_id: int, file_type: FileTypeEnum) -> SongFile | None:
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.song_id == song_id,
                    self.model.file_type == file_type,
                    self.model.is_primary.is_(True),
                )
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def set_primary(self, song_file: SongFile) -> SongFile:
        """Mark ``song_file`` as primary, clearing any existing primary for the same song & file_type.
        """
        existing = self.get_primary(song_file.song_id, song_file.file_type)
        if existing and existing.id != song_file.id:
            existing.is_primary = False
        song_file.is_primary = True
        self.session.flush()
        return song_file

    # ---------------------------------------------------------------------
    # Version handling
    # ---------------------------------------------------------------------
    def next_version(self, song_id: int, file_type: FileTypeEnum) -> int:
        """Return the next sequential version number for a given song and file type.
        Versions start at 1.
        """
        stmt = (
            select(func.max(self.model.version))
            .where(self.model.song_id == song_id, self.model.file_type == file_type)
        )
        max_version = self.session.execute(stmt).scalar_one()
        return (max_version or 0) + 1

    # ---------------------------------------------------------------------
    # Bulk event ingestion helper (delegated to SongEventRepository)
    # ---------------------------------------------------------------------
    # The actual bulk insertion of events is handled by ``SongEventRepository``.
