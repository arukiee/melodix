from pydantic import BaseModel
from typing import Optional

class SearchResult(BaseModel):
    id: str
    title: str
    artist: str
    provider: str
    difficulty: str
    hasMidi: bool
    hasChords: bool
    hasSheetMusic: bool = False
    duration: Optional[int] = None
    popularity: int = 0
    thumbnailUrl: Optional[str] = None
    rank_score: float = 0.0
    low_confidence_match: Optional[bool] = None

class SearchFilter(BaseModel):
    difficulty: Optional[str] = None
    genre: Optional[str] = None
    instrument: Optional[str] = None
    hasMidi: Optional[bool] = None
    hasChords: Optional[bool] = None
    beginnerFriendly: Optional[bool] = None
    limit: int = 10
