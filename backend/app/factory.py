import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .middleware.request_id import RequestIDMiddleware
from .middleware.logging_middleware import StructuredLoggingMiddleware
from .api.v1.health import router as health_router
from .api.auth import router as auth_router
from .api.users import router as users_router
from .api.social import router as social_router
from .api.songs import router as songs_router
from .api.lessons import router as lessons_router
from .api.ai import router as ai_router
from .api.curriculum import router as curriculum_router
from .api.instruments import router as instruments_router
from .api.practice import router as practice_router
from .api.analysis import router as analysis_router
from .api.import_song import router as import_router

logger = logging.getLogger("melodix.factory")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Melodix application lifespan...")
    yield
    logger.info("Shutting down Melodix application lifespan...")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=lifespan
    )

    # Add Middleware
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(StructuredLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include Routers
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(social_router)
    app.include_router(songs_router)
    app.include_router(lessons_router)
    app.include_router(ai_router)
    app.include_router(curriculum_router, prefix="/api/v1")
    app.include_router(instruments_router)
    app.include_router(practice_router, prefix="/api/v1")
    app.include_router(analysis_router, prefix="/api/v1")
    app.include_router(import_router)

    return app

