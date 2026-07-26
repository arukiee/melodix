"""Dependency utilities for API v1 routes."""

from fastapi import Depends
from ...security.dependencies import get_current_user

current_user = Depends(get_current_user)
