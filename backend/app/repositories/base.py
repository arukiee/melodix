# backend/app/repositories/base.py
"""Canonical generic repository abstraction.

All concrete repositories should inherit from ``BaseRepository[Model]``.
The class provides:
* Typed CRUD signatures.
* Session management (self.session).
* Optional logging hooks (``log`` method – can be overridden).
* Transaction helpers (``commit`` / ``rollback``).
* Pagination helpers (``list`` already supports offset/limit).
* Soft‑delete support can be added by subclasses.

Keeping the repository layer consistent prevents duplication and makes
future extensions (e.g., audit logging, caching) straightforward.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, Sequence, TypeVar
import logging

# Generic type for the model handled by the repository
T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Generic abstract base class for all repositories.

    Subclass must define the ``model`` attribute pointing to the SQLAlchemy
    model class and may override any of the hook methods.
    """

    #: Subclasses should set this to the SQLAlchemy model class they manage.
    model: Any

    def __init__(self, session: Any) -> None:
        self.session = session
        self._logger = logging.getLogger(self.__class__.__name__)

    # ---------------------------------------------------------------------
    # Optional hook – can be overridden to add structured logging
    # ---------------------------------------------------------------------
    def log(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit a debug log entry. Subclasses can customise logging format.
        """
        self._logger.debug(message, *args, **kwargs)

    # ---------------------------------------------------------------------
    # Transaction helpers – simple wrappers around the SQLAlchemy session
    # ---------------------------------------------------------------------
    def commit(self) -> None:
        """Commit the current transaction.
        """
        self.session.commit()

    def rollback(self) -> None:
        """Rollback the current transaction.
        """
        self.session.rollback()

    # ---------------------------------------------------------------------
    # CRUD interface – concrete repositories must implement these methods.
    # ---------------------------------------------------------------------
    @abstractmethod
    def get(self, id: Any) -> T:
        """Return a single entity identified by its primary key.
        """
        raise NotImplementedError

    @abstractmethod
    def list(self, offset: int = 0, limit: int = 100) -> Sequence[T]:
        """Return a collection of entities.
        Subclasses can extend the signature with ``filters`` or ``order_by``.
        """
        raise NotImplementedError

    @abstractmethod
    def create(self, obj: T) -> T:
        """Persist a new entity and return it.
        """
        raise NotImplementedError

    @abstractmethod
    def update(self, obj: T) -> T:
        """Persist changes to an existing entity and return it.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, obj: T, soft: bool = False) -> None:
        """Delete an entity.
        If ``soft`` is True, subclasses that support soft‑delete should mark the
        record as inactive rather than removing it.
        """
        raise NotImplementedError
