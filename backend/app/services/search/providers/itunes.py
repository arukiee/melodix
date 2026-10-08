"""
iTunes Search API Provider.

Uses Apple's free public iTunes Search API — no API key or account required.
Same catalog as Apple Music. Returns album art, duration, genre, and artist metadata.

API docs: https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/
"""

import logging
import httpx
from typing import List, Optional

from app.services.search.base_provider import BaseSearchProvider
from app.schemas.search import SearchResult, SearchFilter

logger = logging.getLogger("melodix.search.itunes")


class ITunesProvider(BaseSearchProvider):
    BASE_URL = "https://itunes.apple.com/search"

    @property
    def provider_name(self) -> str:
        return "Apple Music"

    async def search(
        self, query: str, filters: Optional[SearchFilter] = None, **kwargs
    ) -> List[SearchResult]:
        limit = getattr(filters, "limit", 10) or 10
        limit = max(1, min(limit, 20))  # iTunes max is 200 but we cap at 20

        params = {
            "term": query,
            "media": "music",
            "entity": "song",
            "limit": limit,
            "country": "US",
        }

        try:
            logger.info(f"Querying Apple Music / iTunes API: url='{self.BASE_URL}', term='{query}', limit={limit}")
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(self.BASE_URL, params=params)
                logger.info(f"iTunes API HTTP response: status={resp.status_code} for term='{query}'")
                resp.raise_for_status()
                data = resp.json()
                raw_count = len(data.get("results", []))
                logger.info(f"iTunes API returned {raw_count} raw items for term='{query}'")
        except Exception as exc:
            logger.error(f"iTunes API search error for '{query}': {exc}")
            raise exc

        results: List[SearchResult] = []
        for track in data.get("results", []):
            # Skip non-song results (podcasts, audiobooks, etc.)
            if track.get("kind") != "song" and track.get("wrapperType") != "track":
                continue

            duration_ms = track.get("trackTimeMillis", 0)
            duration_secs = int(duration_ms / 1000) if duration_ms else None

            # Upgrade thumbnail from 100px to 300px
            artwork = track.get("artworkUrl100", "")
            if artwork:
                artwork = artwork.replace("100x100bb", "300x300bb")

            results.append(
                SearchResult(
                    id=str(track.get("trackId", "")),
                    title=track.get("trackName", "Unknown Title"),
                    artist=track.get("artistName", "Unknown Artist"),
                    provider=self.provider_name,
                    difficulty="Beginner",
                    hasMidi=False,
                    hasChords=False,
                    hasSheetMusic=False,
                    duration=duration_secs,
                    popularity=int(track.get("trackPrice", 0) * 10),  # rough proxy
                    thumbnailUrl=artwork or None,
                    rank_score=0.0,
                )
            )

        return results

    async def get_raw_data(self, item_id: str) -> bytes:
        raise NotImplementedError(
            "iTunes provider returns metadata only; use YouTube provider to download audio."
        )


itunes_provider = ITunesProvider()
