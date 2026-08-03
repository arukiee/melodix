import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.logging_middleware import StructuredLoggingMiddleware
from app.api.v1.health import router as health_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.social import router as social_router
from app.api.songs import router as songs_router
from app.api.lessons import router as lessons_router
from app.api.ai import router as ai_router
from app.api.curriculum import router as curriculum_router

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
    app.include_router(curriculum_router)

    return app

