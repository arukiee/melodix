"""Base service class – all services inherit from this to get the DB session."""

class BaseService:
    def __init__(self, repository):
        self.repo = repository
