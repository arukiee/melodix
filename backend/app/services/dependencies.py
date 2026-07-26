# backend/app/services/dependencies.py
"""Factory helpers for dependency injection.
Each function returns an instance of the corresponding service bound to the
provided SQLAlchemy ``Session``. FastAPI's ``Depends`` can use these factories
so routers stay thin and testable.
"""

from sqlalchemy.orm import Session

from .song import SongService
from .file import FileService
from .event import EventService
from .difficulty import DifficultyService
from .technique import TechniqueService
from .skill import SkillService
from .analytics import AnalyticsService


def get_song_service(db: Session) -> SongService:
    return SongService(db)


def get_file_service(db: Session) -> FileService:
    return FileService(db)


def get_event_service(db: Session) -> EventService:
    return EventService(db)


def get_difficulty_service(db: Session) -> DifficultyService:
    return DifficultyService(db)


def get_technique_service(db: Session) -> TechniqueService:
    return TechniqueService(db)


def get_skill_service(db: Session) -> SkillService:
    return SkillService(db)


def get_analytics_service(db: Session) -> AnalyticsService:
    return AnalyticsService(db)
