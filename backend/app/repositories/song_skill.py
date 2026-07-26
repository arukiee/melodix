# backend/app/repositories/song_skill.py
"""Repository for the many‑to‑many association between Song and Skill.
Provides CRUD for the junction table and bulk assignment helpers.
All methods return raw SQLAlchemy model instances.
"""

from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.songs import song_skill  # association table defined in models


class SongSkillRepository(BaseRepository[song_skill]):
    """Concrete repository for the ``song_skill`` association table.

    The underlying table does not have a dedicated model class, but SQLAlchemy
    treats the ``song_skill`` Table object as a mapped class when reflected.
    """

    model = song_skill

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def replace_for_song(self, song_id: int, skill_ids: List[int]) -> List[song_skill]:
        """Replace all skill links for a given song.
        Existing rows are deleted and new ones created from ``skill_ids``.
        Returns the list of created association objects.
        """
        # Delete existing links
        self.session.query(self.model).filter(self.model.c.song_id == song_id).delete(synchronize_session=False)
        # Create new links
        new_links = [{"song_id": song_id, "skill_id": sid} for sid in skill_ids]
        return self.bulk_create(new_links)
