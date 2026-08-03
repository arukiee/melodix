# backend/app/services/dependencies.py
"""Factory helpers for dependency injection.
Each function returns an instance of the corresponding service bound to the
provided SQLAlchemy ``Session``. FastAPI's ``Depends`` can use these factories
so routers stay thin and testable.
"""

from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db

from .song import SongService
from .file import FileService
from .auth_service import AuthService

def get_song_service(db: Session) -> SongService:
    return SongService(db)

def get_file_service(db: Session) -> FileService:
    return FileService(db)

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)
