# backend/app/repositories/song_technique.py
"""Repository for the SongTechnique association (Song ↔ Technique).
Provides CRUD for the junction table and helper methods for bulk assignment.
All methods return raw SQLAlchemy model instances.
"""

from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.songs import SongTechnique


class SongTechniqueRepository(BaseRepository[SongTechnique]):
    """Concrete repository for :class:`backend.app.models.songs.SongTechnique`."""

    model = SongTechnique

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def replace_for_song(self, song_id: int, technique_ids: List[int]) -> List[SongTechnique]:
        """Delete existing links for the song and create new ones from ``technique_ids``.
        Returns the list of created ``SongTechnique`` objects.
        """
        # Delete existing links
        self.session.query(self.model).filter(self.model.song_id == song_id).delete(synchronize_session=False)
        # Create new links
        new_links = [{"song_id": song_id, "technique_id": tid} for tid in technique_ids]
        return self.bulk_create(new_links)
