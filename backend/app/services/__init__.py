# backend/app/services/__init__.py
"""Service layer package for the Songs domain.
Exports concrete service classes for easy import.
"""

# Import only the services that actually exist in the codebase.
from .auth_service import AuthService
from .file import FileService
from .song import SongService
