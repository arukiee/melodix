"""High‑level AI orchestrator placeholder."""

from abc import ABC, abstractmethod

class AIOrchestrator(ABC):
    @abstractmethod
    async def handle(self, user_id: str, request: dict) -> dict:
        raise NotImplementedError
