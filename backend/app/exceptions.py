# backend/app/exceptions.py
"""Domain specific exception hierarchy for the Songs domain.
All exceptions inherit from ``DomainError`` so the API layer can map them
to appropriate HTTP responses without importing FastAPI internals.
"""

class DomainError(RuntimeError):
    """Base class for all domain‑level errors."""
    pass

class NotFoundError(DomainError):
    """Raised when an entity cannot be found by its identifier."""
    pass

class AlreadyExistsError(DomainError):
    """Raised when attempting to create a duplicate record that must be unique."""
    pass

class InvalidSongStateError(DomainError):
    """Raised when a song is in a state that does not allow the requested operation."""
    pass

class PrimaryFileConflictError(DomainError):
    """Raised when a primary file already exists for a song and another is being set as primary."""
    pass

class InvalidFileTypeError(DomainError):
    """Raised when an uploaded file's extension or MIME type is not allowed."""
    pass

class InvalidEventPayloadError(DomainError):
    """Raised when event ingestion payload fails validation (e.g., negative timestamps)."""
    pass

class ValidationError(DomainError):
    """Generic validation error for business‑logic constraints."""
    pass
