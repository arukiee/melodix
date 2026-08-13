from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.song import Song
from app.services.search.base_provider import BaseSearchProvider
from app.schemas.search import SearchResult, SearchFilter

class LocalDBProvider(BaseSearchProvider):
    @property
    def provider_name(self) -> str:
        return "Local Library"
        
    async def search(self, query: str, filters: Optional[SearchFilter] = None, **kwargs) -> List[SearchResult]:
        db: Session = kwargs.get("db")
        if not db:
            return []
            
        local_query = db.query(Song).filter(
            or_(
                Song.title.ilike(f"%{query}%"),
                Song.artist.ilike(f"%{query}%"),
                Song.composer.ilike(f"%{query}%")
            )
        )
        
        # Apply filters if any
        if filters:
            if filters.difficulty:
                local_query = local_query.filter(Song.difficulty.ilike(filters.difficulty))
            if filters.genre:
                local_query = local_query.filter(Song.genre.ilike(filters.genre))
                
        local_results = local_query.all()
        
        return [
            SearchResult(
                id=str(song.id),
                title=song.title,
                artist=song.artist or song.composer or "Unknown",
                provider=self.provider_name,
                difficulty=song.difficulty.lower() if song.difficulty else "medium",
                hasMidi=song.source_type == "MIDI",
                hasChords=True, # Assuming local DB has generated chords
                hasSheetMusic=song.source_type == "MUSICXML",
                duration=song.duration,
                popularity=100, # Local files are most relevant
                thumbnailUrl=song.thumbnail_url
            )
            for song in local_results
        ]

    async def get_raw_data(self, item_id: str) -> bytes:
        raise NotImplementedError("Local DB Provider already has processed data; import pipeline not needed.")

local_db_provider = LocalDBProvider()
