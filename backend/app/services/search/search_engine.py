import asyncio
from typing import List, Optional
from sqlalchemy.orm import Session
import difflib

from app.schemas.search import SearchResult, SearchFilter
from app.services.search.base_provider import BaseSearchProvider

class SearchEngine:
    def __init__(self):
        self.providers: List[BaseSearchProvider] = []
        
    def register_provider(self, provider: BaseSearchProvider):
        self.providers.append(provider)
        
    def get_provider(self, name: str) -> Optional[BaseSearchProvider]:
        for p in self.providers:
            if p.provider_name == name:
                return p
        return None
        
    async def search(self, query: str, filters: Optional[SearchFilter] = None, db: Optional[Session] = None) -> List[SearchResult]:
        """
        Concurrently searches all registered providers with a timeout.
        """
        results: List[SearchResult] = []
        
        # Concurrently search
        tasks = []
        for provider in self.providers:
            # We use a 3.0 second timeout for external providers to ensure the UI feels snappy
            task = asyncio.create_task(self._safe_search(provider, query, filters, db))
            tasks.append(task)
            
        provider_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res_list in provider_results:
            if isinstance(res_list, list):
                results.extend(res_list)
                
        # Apply smart ranking
        ranked_results = self._rank_results(query, results)
        return ranked_results

    async def _safe_search(self, provider: BaseSearchProvider, query: str, filters: Optional[SearchFilter], db: Optional[Session]) -> List[SearchResult]:
        try:
            return await asyncio.wait_for(provider.search(query, filters, db=db), timeout=5.0)
        except asyncio.TimeoutError:
            print(f"Provider {provider.provider_name} timed out.")
            return []
        except Exception as e:
            print(f"Provider {provider.provider_name} failed: {e}")
            return []
            
    def _rank_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        query_lower = query.lower()
        
        for res in results:
            score = 0.0
            
            res_title_lower = res.title.lower()
            res_artist_lower = res.artist.lower()
            
            # Exact matches get huge boost
            if query_lower == res_title_lower:
                score += 50
            if query_lower in res_title_lower:
                score += 20
                
            # Fuzzy match title using standard difflib
            title_ratio = difflib.SequenceMatcher(None, query_lower, res_title_lower).ratio()
            score += (title_ratio * 30) # max 30 points
            
            # Fuzzy match artist
            artist_ratio = difflib.SequenceMatcher(None, query_lower, res_artist_lower).ratio()
            score += (artist_ratio * 15)
            
            # Feature boosts
            if res.hasMidi:
                score += 25
            if res.hasChords:
                score += 15
                
            # Popularity/Source trust boost
            if res.provider == "Local Library":
                score += 40 # Always prefer local
            elif res.provider == "Ultimate Guitar":
                score += 10
            elif res.provider == "YouTube":
                score += 5
                
            score += (res.popularity * 0.1) # max 10 points
            
            res.rank_score = score
            
        # Sort descending by rank_score
        return sorted(results, key=lambda x: x.rank_score, reverse=True)

# Global singleton
search_engine = SearchEngine()

from app.services.search.providers.local_db import local_db_provider
from app.services.search.providers.ultimate_guitar import ultimate_guitar_provider
from app.services.search.providers.youtube import youtube_provider
from app.services.search.providers.bitmidi import bitmidi_provider

search_engine.register_provider(local_db_provider)
search_engine.register_provider(ultimate_guitar_provider)
search_engine.register_provider(youtube_provider)
search_engine.register_provider(bitmidi_provider)
