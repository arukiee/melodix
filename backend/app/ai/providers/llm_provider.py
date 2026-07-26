"""Abstract LLM provider interface."""

from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError
