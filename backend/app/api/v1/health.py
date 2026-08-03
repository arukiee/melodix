import time
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/live")
def liveness_probe():
    """Fast container liveness probe."""
    return {"status": "ok", "timestamp": time.time()}

@router.get("/ready")
async def readiness_probe(db: Session = Depends(get_db)):
    """Deep readiness probe checking database, redis, and AI dependencies."""
    services = {}
    overall_status = "healthy"

    # 1. PostgreSQL Check
    try:
        t0 = time.time()
        db.execute(text("SELECT 1"))
        db_latency = round((time.time() - t0) * 1000, 2)
        services["postgresql"] = {"status": "up", "latency_ms": db_latency}
    except Exception as exc:
        services["postgresql"] = {"status": "down", "error": str(exc)}
        overall_status = "unhealthy"

    # 2. Redis Check
    try:
        t0 = time.time()
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=1.0)
        r.ping()
        redis_latency = round((time.time() - t0) * 1000, 2)
        services["redis"] = {"status": "up", "latency_ms": redis_latency}
    except Exception as exc:
        services["redis"] = {"status": "degraded", "error": str(exc)}

    # 3. Ollama AI Check
    try:
        t0 = time.time()
        async with httpx.AsyncClient(timeout=1.5) as client:
            resp = await client.get(f"{settings.OLLAMA_HOST}/api/tags")
            ollama_latency = round((time.time() - t0) * 1000, 2)
            services["ollama"] = {"status": "up" if resp.status_code == 200 else "degraded", "latency_ms": ollama_latency}
    except Exception as exc:
        services["ollama"] = {"status": "degraded", "error": str(exc)}

    return {
        "status": overall_status,
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "services": services,
        "timestamp": time.time()
    }
