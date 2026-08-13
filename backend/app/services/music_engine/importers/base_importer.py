from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseImporter(ABC):
    @abstractmethod
    def parse(self, file_content: bytes) -> Dict[str, Any]:
        """
        Parses raw bytes of a music file and returns a structured dictionary
        representing the metadata, notes, measures, and musical attributes.
        """
        pass
