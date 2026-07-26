"""Base repository providing generic CRUD helpers."""

from abc import ABC, abstractmethod

class BaseRepository(ABC):
    def __init__(self, session):
        self.session = session

    @abstractmethod
    def get(self, id):
        raise NotImplementedError

    @abstractmethod
    def list(self, offset: int = 0, limit: int = 100):
        raise NotImplementedError

    @abstractmethod
    def create(self, obj):
        raise NotImplementedError

    @abstractmethod
    def update(self, obj):
        raise NotImplementedError

    @abstractmethod
    def delete(self, obj):
        raise NotImplementedError
