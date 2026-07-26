# backend/app/services/file.py
"""FileService handles validation and management of SongFile records.
It enforces business rules such as:
* Allowed extensions and mime types
* Placeholder size validation (to be replaced with real limits)
* Generation of sequential version numbers per song
* Exactly one primary file per song (promotion/demotion logic)
* Storage URI validation hook (e.g., S3 bucket path format)
* File replacement workflow (add new version, optionally replace existing)
"""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..repositories.song_file import SongFileRepository
from ..repositories.song import SongRepository
from ..exceptions import ValidationError, NotFoundError

# Define allowed extensions and corresponding MIME types.
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".flac", ".mid", ".midi", ".xml"}
# Map extensions to a set of acceptable MIME types (simplified).
EXTENSION_MIME_MAP = {
    ".wav": {"audio/wav"},
    ".mp3": {"audio/mpeg"},
    ".flac": {"audio/flac"},
    ".mid": {"audio/midi", "audio/mid"},
    ".midi": {"audio/midi", "audio/mid"},
    ".xml": {"application/xml", "text/xml"},
}

# Placeholder maximum file size in bytes (e.g., 50 MB).
MAX_FILE_SIZE = 50 * 1024 * 1024


class FileService:
    """Service responsible for SongFile business rules.

    All methods receive a ``Session`` that is **not** committed here – the caller
    (usually a FastAPI endpoint) handles the transaction boundaries.
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = SongFileRepository(session)
        self.song_repo = SongRepository(session)

    # ---------------------------------------------------------------------
    # Helper validation utilities
    # ---------------------------------------------------------------------
    def _validate_extension(self, filename: str) -> None:
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(f"File extension '{ext}' is not allowed. Allowed: {sorted(ALLOWED_EXTENSIONS)}")

    def _validate_mime(self, filename: str, mime_type: str) -> None:
        ext = Path(filename).suffix.lower()
        allowed_mimes = EXTENSION_MIME_MAP.get(ext, set())
        if mime_type not in allowed_mimes:
            raise ValidationError(
                f"MIME type '{mime_type}' does not match allowed types for '{ext}': {sorted(allowed_mimes)}"
            )

    def _validate_size(self, size: int) -> None:
        if size > MAX_FILE_SIZE:
            raise ValidationError(f"File size {size} exceeds maximum of {MAX_FILE_SIZE} bytes")

    def _validate_storage_uri(self, uri: str) -> None:
        # Simple hook – ensure it looks like an S3 or local path.
        if not (uri.startswith("s3://") or uri.startswith("file://")):
            raise ValidationError("Storage URI must start with 's3://' or 'file://'")

    # ---------------------------------------------------------------------
    # Core public API
    # ---------------------------------------------------------------------
    def add_file(self, *, song_id: int, filename: str, mime_type: str, size: int, uri: str, is_primary: bool = False, **extra: Any) -> "SongFile":
        """Validate and create a new ``SongFile`` record.

        * ``song_id`` must reference an existing non‑deleted song.
        * ``filename`` is checked for allowed extension.
        * ``mime_type`` must correspond to the extension.
        * ``size`` is validated against ``MAX_FILE_SIZE``.
        * ``uri`` is validated by ``_validate_storage_uri``.
        * If ``is_primary`` is ``True``, any existing primary file for the song
          is demoted to ``False`` so that exactly one primary file exists.
        """
        # Verify song exists (including soft‑deleted check)
        song = self.song_repo.get_or_raise(song_id)
        if getattr(song, "deleted_at", None) is not None:
            raise ValidationError("Cannot add a file to a soft‑deleted song")

        # Run validation helpers
        self._validate_extension(filename)
        self._validate_mime(filename, mime_type)
        self._validate_size(size)
        self._validate_storage_uri(uri)

        # Determine version – the next integer after existing versions for the same song.
        next_version = self._next_version(song_id)

        # Enforce single primary file per song.
        if is_primary:
            self._demote_existing_primary(song_id)

        payload: Dict[str, Any] = {
            "song_id": song_id,
            "filename": filename,
            "mime_type": mime_type,
            "size": size,
            "uri": uri,
            "is_primary": is_primary,
            "version": next_version,
            **extra,
        }
        return self.repo.create(payload)

    def replace_file(self, file_id: int, *, filename: str, mime_type: str, size: int, uri: str, **extra: Any) -> "SongFile":
        """Replace an existing file with a new version.
        This creates a **new** ``SongFile`` record (preserving history) and
        optionally promotes it to primary if the old file was primary.
        """
        old_file = self.repo.get_by_id(file_id)
        if not old_file:
            raise NotFoundError(f"SongFile with id {file_id} not found")
        # Validate new data
        self._validate_extension(filename)
        self._validate_mime(filename, mime_type)
        self._validate_size(size)
        self._validate_storage_uri(uri)

        # Increment version for the same song
        next_version = self._next_version(old_file.song_id)
        is_primary = old_file.is_primary
        if is_primary:
            self._demote_existing_primary(old_file.song_id)

        payload = {
            "song_id": old_file.song_id,
            "filename": filename,
            "mime_type": mime_type,
            "size": size,
            "uri": uri,
            "is_primary": is_primary,
            "version": next_version,
            **extra,
        }
        return self.repo.create(payload)

    def promote_to_primary(self, file_id: int) -> "SongFile":
        """Make the given file the primary version for its song.
        Any other primary file for the same song is demoted.
        """
        file_obj = self.repo.get_by_id(file_id)
        if not file_obj:
            raise NotFoundError(f"SongFile with id {file_id} not found")
        # Demote existing primary if different
        self._demote_existing_primary(file_obj.song_id, exclude_id=file_id)
        return self.repo.update(file_obj, {"is_primary": True})

    def demote_primary(self, file_id: int) -> "SongFile":
        """Demote a primary file – the caller must ensure another primary will be set.
        """
        file_obj = self.repo.get_by_id(file_id)
        if not file_obj:
            raise NotFoundError(f"SongFile with id {file_id} not found")
        if not getattr(file_obj, "is_primary", False):
            return file_obj  # Already not primary
        return self.repo.update(file_obj, {"is_primary": False})

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _next_version(self, song_id: int) -> int:
        """Return the next integer version for a given song.
        Versions start at 1 and increment monotonically.
        """
        stmt = (
            self.session.query(self.repo.model.version)
            .filter(self.repo.model.song_id == song_id)
            .order_by(self.repo.model.version.desc())
            .limit(1)
        )
        result = stmt.first()
        return (result[0] if result else 0) + 1

    def _demote_existing_primary(self, song_id: int, exclude_id: Optional[int] = None) -> None:
        """Set ``is_primary=False`` on all other files for the song.
        ``exclude_id`` can be used to keep a specific file primary.
        """
        query = self.session.query(self.repo.model).filter(
            self.repo.model.song_id == song_id,
            self.repo.model.is_primary.is_(True),
        )
        if exclude_id is not None:
            query = query.filter(self.repo.model.id != exclude_id)
        query.update({"is_primary": False}, synchronize_session=False)
        self.session.flush()

    # ---------------------------------------------------------------------
    # Retrieval helpers (thin wrappers around repository)
    # ---------------------------------------------------------------------
    def get_file(self, file_id: int) -> "SongFile":
        return self.repo.get_or_raise(file_id)

    def list_files(self, *, song_id: Optional[int] = None, include_deleted: bool = False, **filters: Any) -> List["SongFile"]:
        base_filters: Dict[str, Any] = dict(filters)
        if song_id is not None:
            base_filters["song_id"] = song_id
        return list(self.repo.list(filters=base_filters, include_deleted=include_deleted))
