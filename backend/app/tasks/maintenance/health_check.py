from app.celery_app import celery_app
from ..base import BaseTask

@celery_app.task(base=BaseTask, name="maintenance.health_check")
def health_check():
    """Simple health check task returning a consistent OK payload."""
    return {"status": "ok"}
