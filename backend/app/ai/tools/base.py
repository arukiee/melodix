"""Base abstraction for AI tools used by agents."""

from abc import ABC, abstractmethod

class Tool(ABC):
    name: str
    description: str
    input_schema: dict
    output_schema: dict
    permissions: list[str]

    @abstractmethod
    async def run(self, *args, **kwargs):
        raise NotImplementedError
