from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas.search import SearchResult, SearchFilter

class BaseSearchProvider(ABC):
    """
    Abstract base class for all search providers (Local, MIDI, YouTube, UltimateGuitar, etc.).
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'Ultimate Guitar', 'Musescore')."""
        pass
        
    @abstractmethod
    async def search(self, query: str, filters: Optional[SearchFilter] = None, **kwargs) -> List[SearchResult]:
        """
        Search the provider and return a unified list of SearchResults.
        """
        pass

    @abstractmethod
    async def get_raw_data(self, item_id: str) -> bytes:
        """
        Fetch the raw MusicXML or MIDI payload for a given result ID to pass into the import pipeline.
        """
        pass
