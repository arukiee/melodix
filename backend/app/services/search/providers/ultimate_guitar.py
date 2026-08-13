import asyncio
import httpx
import json
import re
from typing import List, Optional
from bs4 import BeautifulSoup
from app.services.search.base_provider import BaseSearchProvider
from app.schemas.search import SearchResult, SearchFilter

class UltimateGuitarProvider(BaseSearchProvider):
    @property
    def provider_name(self) -> str:
        return "Ultimate Guitar"
        
    async def search(self, query: str, filters: Optional[SearchFilter] = None, **kwargs) -> List[SearchResult]:
        try:
            url = f"https://www.ultimate-guitar.com/search.php?search_type=title&value={query}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

            # The data is typically injected into window.UGAPP.store.page
            match = re.search(r'window\.UGAPP\.store\.page\s*=\s*(\{.*?\});', response.text)
            if not match:
                return []
                
            data = json.loads(match.group(1))
            results_data = data.get('data', {}).get('results', [])
            
            results = []
            for item in results_data:
                if not isinstance(item, dict) or 'song_name' not in item:
                    continue
                
                # Only grab chords/tabs for now
                if item.get('type') not in ['Chords', 'Tab', 'Pro']:
                    continue
                    
                tab_url = item.get('tab_url', '')
                if not tab_url:
                    continue

                results.append(SearchResult(
                    # We store the tab_url as the ID so get_raw_data knows exactly which page to scrape
                    id=tab_url,
                    title=item.get('song_name', 'Unknown Title'),
                    artist=item.get('artist_name', 'Unknown Artist'),
                    provider=self.provider_name,
                    difficulty='Easy',
                    hasMidi=False,
                    hasChords=True,
                    hasSheetMusic=False,
                    duration=180,
                    popularity=item.get('votes', 0),
                    thumbnailUrl='',
                    rank_score=0.0
                ))
            return results
        except Exception as e:
            print(f"Ultimate Guitar search error: {e}")
            return []

    async def get_raw_data(self, item_id: str) -> bytes:
        """
        Scrapes the Ultimate Guitar chord page, extracts the raw chords/lyrics block from the page JSON,
        and returns it as UTF-8 bytes.
        """
        try:
            # item_id is the full tab_url we stored during search
            if not item_id.startswith("http"):
                return b"MOCK_CHORD_DATA"

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            async with httpx.AsyncClient() as client:
                res = await client.get(item_id, headers=headers)
                res.raise_for_status()

            match = re.search(r'window\.UGAPP\.store\.page\s*=\s*(\{.*?\});', res.text)
            if not match:
                return b"MOCK_CHORD_DATA"
                
            data = json.loads(match.group(1))
            wiki_tab = data.get('data', {}).get('tab_view', {}).get('wiki_tab', {})
            content = wiki_tab.get('content', '')
            
            if not content:
                # Fallback to search for content block inside general data
                content = data.get('data', {}).get('tab', {}).get('content', '')

            if content:
                return content.encode('utf-8')

            return b"MOCK_CHORD_DATA"
        except Exception as e:
            print(f"Ultimate Guitar content scrape error: {e}")
            return b"MOCK_CHORD_DATA"

ultimate_guitar_provider = UltimateGuitarProvider()
