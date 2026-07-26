# backend/app/services/song.py
"""Song service orchestrating business logic for the Song aggregate.
All methods accept a SQLAlchemy ``Session`` that is managed by the caller
(e.g., a FastAPI endpoint) so transaction boundaries remain explicit.
The service uses the repository layer for pure data access and raises the
custom domain exceptions defined in ``backend.app.exceptions``.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from ..repositories.song import SongRepository
from ..repositories.song_file import SongFileRepository
from ..repositories.song_difficulty import SongDifficultyRepository
from ..repositories.song_technique import SongTechniqueRepository
from ..repositories.song_skill import SongSkillRepository
from ..repositories.song_analytics import SongAnalyticsRepository

from ..exceptions import (
    AlreadyExistsError,
    NotFoundError,
    InvalidSongStateError,
    ValidationError,
)


class SongService:
    """High‑level service for creating, updating and managing songs.
    The service does **not** commit or roll back the session – the caller
    is responsible for transaction handling (``with session.begin():``).
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = SongRepository(session)
        self.file_repo = SongFileRepository(session)
        self.diff_repo = SongDifficultyRepository(session)
        self.tech_repo = SongTechniqueRepository(session)
        self.skill_repo = SongSkillRepository(session)
        self.analytics_repo = SongAnalyticsRepository(session)

    # ---------------------------------------------------------------------
    # CRUD operations
    # ---------------------------------------------------------------------
    def create_song(self, data: dict) -> "Song":
        """Create a new song record.
        ``data`` should contain the fields required by the ``SongCreate`` schema.
        Raises ``AlreadyExistsError`` if a song with the same title and creator
        already exists.
        """
        if self.repo.exists(title=data.get("title"), created_by=data.get("created_by")):
            raise AlreadyExistsError("A song with this title already exists for the user")
        song = self.repo.create(data)
        # Create a default difficulty record so the one‑to‑one relation is present.
        self.diff_repo.create({"song_id": song.id, "difficulty_level": 1})
        return song

    def get_song(self, song_id: int, include_deleted: bool = False) -> "Song":
        return self.repo.get_or_raise(song_id, include_deleted=include_deleted)

    def update_song(self, song_id: int, data: dict) -> "Song":
        song = self.get_song(song_id)
        if getattr(song, "deleted_at", None) is not None:
            raise InvalidSongStateError("Cannot update a soft‑deleted song")
        return self.repo.update(song, data)

    # ---------------------------------------------------------------------
    # Soft‑delete (archive) and restore
    # ---------------------------------------------------------------------
    def archive_song(self, song_id: int) -> "Song":
        song = self.get_song(song_id)
        return self.repo.archive(song)

    def restore_song(self, song_id: int) -> "Song":
        song = self.get_song(song_id, include_deleted=True)
        return self.repo.restore(song)

    # ---------------------------------------------------------------------
    # Publication helpers
    # ---------------------------------------------------------------------
    def publish_song(self, song_id: int, published_at: Optional[datetime] = None) -> "Song":
        song = self.get_song(song_id)
        if song.is_public:
            raise ValidationError("Song is already public")
        published_at = published_at or datetime.utcnow()
        return self.repo.publish(song, published_at)

    def unpublish_song(self, song_id: int) -> "Song":
        song = self.get_song(song_id)
        if not song.is_public:
            raise ValidationError("Song is already not public")
        return self.repo.unpublish(song)

    # ---------------------------------------------------------------------
    # Related entity synchronization
    # ---------------------------------------------------------------------
    def set_difficulty(self, song_id: int, level: int, notes: Optional[str] = None) -> "SongDifficulty":
        diff = self.diff_repo.get_by_id(song_id, include_deleted=False)  # one‑to‑one uses song_id as PK
        payload = {"difficulty_level": level, "notes": notes}
        if diff:
            return self.diff_repo.update(diff, payload)
        payload["song_id"] = song_id
        return self.diff_repo.create(payload)

    def replace_techniques(self, song_id: int, technique_ids: List[int]) -> List["SongTechnique"]:
        return self.tech_repo.replace_for_song(song_id, technique_ids)

    def replace_skills(self, song_id: int, skill_ids: List[int]) -> List["SongSkill"]:
        return self.skill_repo.replace_for_song(song_id, skill_ids)

    # ---------------------------------------------------------------------
    # File handling delegation (the FileService contains the validation logic)
    # ---------------------------------------------------------------------
    def add_file(self, file_data: dict) -> "SongFile":
        return self.file_repo.create(file_data)

    # ---------------------------------------------------------------------
    # Analytics queueing – delegated to an AnalyticsService instance
    # ---------------------------------------------------------------------
    def queue_analytics(self, song_id: int, analytics_service: "AnalyticsService") -> None:
        analytics_service.queue_recompute(song_id)
