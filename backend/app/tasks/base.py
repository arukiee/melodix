from celery import Task
import logging
import time
from celery.signals import task_prerun, task_postrun

logger = logging.getLogger("celery")

class BaseTask(Task):
    # Centralised retry configuration – Celery will use these defaults unless a task overrides them
    autoretry_for = (Exception,)
    retry_backoff = True          # exponential back‑off
    retry_backoff_max = 600       # max back‑off 10 minutes
    retry_jitter = True           # add jitter to avoid thundering herd
    retry_kwargs = {"max_retries": 3}
    default_retry_delay = 5       # seconds, overridden by back‑off logic

    def on_success(self, retval, task_id, args, kwargs):
        logger.info(
            "Task succeeded",
            extra={"task_id": task_id, "task": self.name, "result": retval},
        )
        super().on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(
            "Task failed",
            extra={"task_id": task_id, "task": self.name, "exception": str(exc)},
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)

# Timing via signals – store start time in task request
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    task.request.start_time = time.time()

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, retval=None, state=None, **kwargs):
    duration = time.time() - getattr(task.request, "start_time", time.time())
    logger.info(
        "Task finished",
        extra={"task_id": task_id, "task": task.name, "duration": duration, "state": state},
    )
