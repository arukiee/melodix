import asyncio
from typing import List, Dict

class YouTubeProvider:
    """
    Mock provider for YouTube search.
    In a real implementation, this would use the YouTube Data API or youtube-dl/yt-dlp
    to search for videos and extract metadata/audio.
    """
    
    async def search(self, query: str) -> List[Dict]:
        # Simulate network delay
        await asyncio.sleep(0.6)
        
        # Mock results
        return [
            {
                "id": f"yt_mock_{query.replace(' ', '_').lower()}_1",
                "title": f"{query.title()} (Piano Cover/Tutorial)",
                "artist": "PianoTuber",
                "source": "YouTube",
                "difficulty": "hard",
                "thumbnailUrl": "https://images.unsplash.com/photo-1552422535-c45813c61732?auto=format&fit=crop&w=300&q=80",
                "url": f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}+piano",
                "timeline_data": [
                    {"id": "note-1", "note": "G4", "startTime": 0, "duration": 0.5, "velocity": 85},
                    {"id": "note-2", "note": "G4", "startTime": 0.5, "duration": 0.5, "velocity": 85},
                    {"id": "note-3", "note": "D5", "startTime": 1.0, "duration": 0.5, "velocity": 85},
                    {"id": "note-4", "note": "D5", "startTime": 1.5, "duration": 0.5, "velocity": 85},
                    {"id": "note-5", "note": "E5", "startTime": 2.0, "duration": 0.5, "velocity": 85},
                    {"id": "note-6", "note": "E5", "startTime": 2.5, "duration": 0.5, "velocity": 85},
                    {"id": "note-7", "note": "D5", "startTime": 3.0, "duration": 1.0, "velocity": 90}
                ]
            }
        ]

youtube_provider = YouTubeProvider()
