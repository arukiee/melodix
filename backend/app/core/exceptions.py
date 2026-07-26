'''exceptions module for FastAPI application'''

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Import the domain exception hierarchy defined in the top-level exceptions module
from ..exceptions import DomainError


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for the FastAPI application.

    Currently registers a handler for :class:`DomainError` which returns a
    400 Bad Request response with the exception message. Additional handlers
    can be added here as the project grows.
    """

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):
        # Logging could be added here if needed
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    # Fallback handler for unexpected exceptions (optional)
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
