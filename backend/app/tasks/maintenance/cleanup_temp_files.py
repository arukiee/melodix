from app.celery_app import celery_app
from ..base import BaseTask

@celery_app.task(base=BaseTask, name="maintenance.cleanup_temp_files")
def cleanup_temp_files():
    """Placeholder task – performs no action and returns a simple status dict."""
    return {"status": "ok"}
