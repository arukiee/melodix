# backend/app/repositories/song_analytics.py
"""Repository for the SongAnalytics one‑to‑one entity.
Provides simple CRUD; analytics data is generally written by background jobs.
All methods return raw SQLAlchemy model instances.
"""

from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.songs import SongAnalytics


class SongAnalyticsRepository(BaseRepository[SongAnalytics]):
    """Concrete repository for :class:`backend.app.models.songs.SongAnalytics`."""

    model = SongAnalytics

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    # Additional analytics‑specific helpers could be added later (e.g., aggregation).
