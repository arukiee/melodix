# backend/app/logging.py
"""Central logging configuration for the backend.
The configuration is deliberately simple: a JSON‑style formatter emitted to STDOUT.
All service modules import ``logging.getLogger(__name__)`` and rely on this setup.
"""

import logging
import sys
from logging.config import dictConfig

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":%(message)s}',
            "style": "%",
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": sys.stdout,
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["stdout"],
    },
}

# Apply configuration at import time so any module importing ``backend.app.logging``
# will configure the global logging system.

dictConfig(LOGGING_CONFIG)

# Export a convenience function for services that want to obtain a module‑level logger.
def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
