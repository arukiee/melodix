"""Celery task package."""

# Import maintenance tasks so they are discovered when the package is included
from .maintenance.health_check import health_check
from .maintenance.cleanup_temp_files import cleanup_temp_files
from .transcribe_audio import process_audio_pipeline
