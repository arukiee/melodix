# backend/app/api/v1/health.py
"""Health check endpoints for the API version 1."""

from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    """Simple liveness probe returning status OK."""
    return {"status": "ok"}
