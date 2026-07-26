# backend/app/repositories/song_event.py
"""Repository for the SongEvent table (canonical ground‑truth events).
Provides bulk insertion and query helpers.
All methods return raw SQLAlchemy model instances.
"""

from __future__ import annotations

from typing import Iterable, List, Dict

from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.songs import SongEvent


class SongEventRepository(BaseRepository[SongEvent]):
    """Concrete repository for :class:`backend.app.models.songs.SongEvent`."""

    model = SongEvent

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def bulk_create_events(self, events: Iterable[Dict[str, any]]) -> List[SongEvent]:
        """Insert many ``SongEvent`` rows efficiently.
        ``events`` is an iterable of dictionaries matching the model fields.
        Returns the list of created ``SongEvent`` objects.
        """
        return self.bulk_create(events)
