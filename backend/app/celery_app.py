from __future__ import annotations
import logging
from celery import Celery
from .celery_config import CelerySettings

settings = CelerySettings()

celery_app = Celery(
    "melodix",
    broker=settings.broker_url,
    backend=settings.result_backend,
    include=["app.tasks"],  # autodiscover tasks package
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=settings.task_default_retry_delay,
    task_max_retries=settings.task_max_retries,
    beat_schedule=settings.beat_schedule,
)

# Structured JSON logging for Celery workers
logger = logging.getLogger("celery")
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter('{"time":"%(asctime)s","level":"%(levelname)s","task_id":"%(task_id)s","task":"%(task_name)s","msg":"%(message)s"}')
)
logger.handlers = [handler]
logger.setLevel(logging.INFO)
