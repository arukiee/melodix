# backend/app/main.py
"""Application entry point – loads the FastAPI instance from the factory."""

from .factory import create_app

app = create_app()
