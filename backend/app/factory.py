from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .core.exceptions import register_exception_handlers
from .config.settings import settings
from .storage.minio_service import StorageService
from .api.v1.router import router as api_v1_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
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
    async def on_startup() -> None:
        try:
            StorageService()
        except Exception as exc:
            logging.error("MinIO connection failed during startup: %s", exc)
            raise RuntimeError("MinIO connection unavailable") from exc

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        # Placeholder for cleanup logic
        pass

    return app
