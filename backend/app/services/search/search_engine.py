import asyncio
import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
import difflib
from fastapi import HTTPException, status

from app.schemas.search import SearchResult, SearchFilter
from app.services.search.base_provider import BaseSearchProvider

logger = logging.getLogger("melodix.search.engine")

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
        errors: Dict[str, str] = {}
        
        # Concurrently search
        tasks = []
        for provider in self.providers:
            task = asyncio.create_task(self._safe_search(provider, query, filters, db, errors))
            tasks.append(task)
            
        provider_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res_list in provider_results:
            if isinstance(res_list, list):
                results.extend(res_list)
                
        logger.info(f"Search query='{query}': found {len(results)} total results from {len(self.providers)} providers. Failures: {errors}")

        # If no results were found and all external providers failed with network/API errors:
        if not results and errors:
            external_count = len([p for p in self.providers if p.provider_name != "Local Library"])
            failed_external_count = len([k for k in errors if k != "Local Library"])
            if failed_external_count >= external_count and external_count > 0:
                err_details = "; ".join(f"{k}: {v}" for k, v in errors.items())
                logger.error(f"Search query='{query}' failed because all external providers were unreachable: {err_details}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Search services currently unreachable ({err_details}). Please check network connection or try local pieces.",
                )

        # Apply smart ranking
        ranked_results = self._rank_results(query, results)
        return ranked_results

    async def _safe_search(self, provider: BaseSearchProvider, query: str, filters: Optional[SearchFilter], db: Optional[Session], errors: Dict[str, str]) -> List[SearchResult]:
        try:
            res = await asyncio.wait_for(provider.search(query, filters, db=db), timeout=4.0)
            logger.info(f"Provider '{provider.provider_name}' returned {len(res)} results for query='{query}'")
            return res
        except asyncio.TimeoutError:
            err_msg = "Request timed out after 4.0s"
            logger.warning(f"Provider '{provider.provider_name}' timed out for query '{query}'")
            errors[provider.provider_name] = err_msg
            return []
        except Exception as e:
            err_msg = str(e)
            logger.warning(f"Provider '{provider.provider_name}' failed for query '{query}': {err_msg}")
            errors[provider.provider_name] = err_msg
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

from app.services.search.providers.itunes import itunes_provider
search_engine.register_provider(itunes_provider)
