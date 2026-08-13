import asyncio
from typing import List, Dict

class UltimateGuitarProvider:
    """
    Mock provider for Ultimate Guitar chords.
    In a real implementation, this would scrape UG or use an API to fetch chord sheets.
    """
    
    async def search(self, query: str) -> List[Dict]:
        # Simulate network delay
        await asyncio.sleep(0.5)
        
        # Mock results
        return [
            {
                "id": f"ug_mock_{query.replace(' ', '_').lower()}_1",
                "title": query.title(),
                "artist": "Various Artists",
                "source": "Ultimate Guitar",
                "difficulty": "medium",
                "url": f"https://tabs.ultimate-guitar.com/tab/search?q={query.replace(' ', '+')}",
                "timeline_data": [
                    {"id": "note-1", "note": "C4", "startTime": 0, "duration": 0.5, "velocity": 80},
                    {"id": "note-2", "note": "E4", "startTime": 0.5, "duration": 0.5, "velocity": 80},
                    {"id": "note-3", "note": "G4", "startTime": 1.0, "duration": 0.5, "velocity": 80},
                    {"id": "note-4", "note": "C5", "startTime": 1.5, "duration": 1.5, "velocity": 90}
                ]
            }
        ]

ultimate_guitar_provider = UltimateGuitarProvider()
