"""SQLAlchemy engine creation using settings."""

from sqlalchemy import create_engine
from ..config.settings import settings

engine = create_engine(
    settings.DATABASE.url,
    echo=settings.DATABASE.echo,
    pool_size=settings.DATABASE.pool_size,
    max_overflow=settings.DATABASE.max_overflow,
)
