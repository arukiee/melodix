# backend/app/api/exceptions.py
"""Global exception handling for domain errors.
Mapping of custom DomainError subclasses to HTTP status codes is defined
here so routers stay thin and unaware of HTTP concerns.
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from app.exceptions import (
    DomainError,
    NotFoundError,
    AlreadyExistsError,
    ValidationError,
    InvalidSongStateError,
    PrimaryFileConflictError,
    InvalidFileTypeError,
    InvalidEventPayloadError,
)

# Mapping of exception class to HTTP status code
_EXCEPTION_STATUS_MAP: dict[type[DomainError], int] = {
    NotFoundError: 404,
    AlreadyExistsError: 409,
    ValidationError: 400,
    InvalidSongStateError: 400,
    PrimaryFileConflictError: 409,
    InvalidFileTypeError: 400,
    InvalidEventPayloadError: 400,
}


async def domain_error_handler(request: Request, exc: DomainError):
    """Convert a DomainError into a JSON HTTP response.

    The response structure is ``{"detail": "<error message>"}`` which matches
    FastAPI's default error format. The appropriate status code is selected
    based on ``_EXCEPTION_STATUS_MAP``; unknown subclasses default to 500.
    """
    status_code = _EXCEPTION_STATUS_MAP.get(type(exc), 500)
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})

# Register the handler when the module is imported. The FastAPI app instance
# is obtained via the ``app`` variable defined in ``backend/main.py``; however,
# importing ``app`` here would create a circular import. Therefore, the
# registration is performed in ``backend/main.py`` where the ``FastAPI``
# instance is created.
