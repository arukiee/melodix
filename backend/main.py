"""Backward-compatible entry point; route registration lives in app.factory."""

from app.main import app

__all__ = ["app"]
