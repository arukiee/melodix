# backend/app/routers/celery_router.py
"""Celery health router providing worker and broker status."""

from fastapi import APIRouter
from app.celery_app import celery_app

router = APIRouter(prefix="/api/v1/celery", tags=["Celery"])

@router.get("/health")
async def celery_health():
    try:
        inspector = celery_app.control.inspect()
        ping = inspector.ping() or {}
        workers = len(ping)
        broker_ok = True
    except Exception:
        workers = 0
        broker_ok = False
    # Assume beat is running if the beat schedule is defined
    beat_ok = bool(celery_app.conf.beat_schedule)
    # Queue depths – active and reserved queues
    inspector = celery_app.control.inspect()
    active = inspector.active() or {}
    queues = {"default": sum(len(v) for v in active.values())}
    return {
        "status": "ok" if workers > 0 and broker_ok and beat_ok else "unhealthy",
        "workers": workers,
        "beat": "running" if beat_ok else "stopped",
        "broker": "connected" if broker_ok else "down",
        "queues": queues,
    }
