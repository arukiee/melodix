# backend/app/factory.py
"""Application factory for creating the FastAPI instance.

Separates app creation from the entry point to improve testability.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import settings
from .core.exceptions import register_exception_handlers
from .api.v1.router import router as api_v1_router


def create_app() -> FastAPI:
    """Create and configure a FastAPI application instance."""
    app = FastAPI(title="Melodix API", version="0.1.0")

    # CORS – allow all origins for development (restrict in production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register global exception handlers
    register_exception_handlers(app)

    # Include versioned API router
    app.include_router(api_v1_router)

    @app.on_event("startup")
    async def on_startup():
        # Placeholder for async initialisation (e.g., DB connections)
        pass

    @app.on_event("shutdown")
    async def on_shutdown():
        # Placeholder for cleanup logic
        pass

    return app
