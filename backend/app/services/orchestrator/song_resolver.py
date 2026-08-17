"""
Song Resolver — cross-provider matching with real confidence.
"""

import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class SongResolver:
    """
    Resolves a requested song by matching metadata across providers
    with deterministic confidence scoring.
    """

    def resolve(self, title_search: str, artist_search: str, db: Session) -> dict:
        """
        Finds the best matching song in the local database.
        Returns the resolved Song record or None.
        """
        from app.models.song import Song

        songs = db.query(Song).all()
        best_match = None
        best_confidence = 0.0

        for song in songs:
            title_sim = SequenceMatcher(None, title_search.lower(), song.title.lower()).ratio()
            
            artist_sim = 0.5
            if artist_search and song.artist:
                artist_sim = SequenceMatcher(None, artist_search.lower(), song.artist.lower()).ratio()

            confidence = (title_sim * 0.7) + (artist_sim * 0.3)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = song

        if best_confidence >= 0.75 and best_match:
            return {
                "resolved_song_id": str(best_match.id),
                "confidence": round(best_confidence, 4),
                "title": best_match.title,
                "artist": best_match.artist
            }
            
        return {
            "resolved_song_id": None,
            "confidence": round(best_confidence, 4)
        }
