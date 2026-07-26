# backend/app/api/v1/router.py
"""Root router for API v1 – includes sub‑routers."""

from fastapi import APIRouter
from .health import router as health_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
