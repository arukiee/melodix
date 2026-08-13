import asyncio
import httpx
import re
from typing import List, Optional
from bs4 import BeautifulSoup
from app.services.search.base_provider import BaseSearchProvider
from app.schemas.search import SearchResult, SearchFilter

class BitMidiProvider(BaseSearchProvider):
    @property
    def provider_name(self) -> str:
        return "BitMidi"
        
    async def search(self, query: str, filters: Optional[SearchFilter] = None, **kwargs) -> List[SearchResult]:
        try:
            url = f"https://bitmidi.com/search?q={query}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # BitMidi renders search results as links like <a href="/something-mid">Something</a>
            results = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('-mid'):
                    title = link.text.strip()
                    # Clean title
                    clean_title = title.replace(".mid", "").replace("-", " ").title()
                    results.append(SearchResult(
                        id=href,
                        title=clean_title,
                        artist="Traditional",
                        provider=self.provider_name,
                        difficulty='Easy',
                        hasMidi=True,
                        hasChords=True,
                        hasSheetMusic=False,
                        duration=120,
                        popularity=100,
                        thumbnailUrl='',
                        rank_score=0.0
                    ))
            
            return results[:10] # Top 10 results
        except Exception as e:
            print(f"BitMidi search error: {e}")
            return []

    async def get_raw_data(self, item_id: str) -> bytes:
        """
        Scrapes the download page for the actual MIDI file download URL and downloads the binary content.
        """
        try:
            url = f"https://bitmidi.com{item_id}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            async with httpx.AsyncClient() as client:
                res = await client.get(url, headers=headers)
                res.raise_for_status()
                
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # Look for the download button. Typically has a direct link containing "/uploads/" or "bitmidi.com/uploads/"
                download_url = None
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if "/uploads/" in href and href.endswith('.mid'):
                        download_url = href
                        break
                
                # Fallback: check if we can construct it or if there's any link ending with .mid
                if not download_url:
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if href.endswith('.mid'):
                            download_url = href
                            break
                            
                if not download_url:
                    # Let's try to match /uploads/xxx.mid in the whole HTML text
                    match = re.search(r'/uploads/[a-zA-Z0-9_\-]+\.mid', res.text)
                    if match:
                        download_url = match.group(0)

                if download_url:
                    # Make absolute if needed
                    if download_url.startswith('/'):
                        download_url = f"https://bitmidi.com{download_url}"
                        
                    file_res = await client.get(download_url, headers=headers)
                    file_res.raise_for_status()
                    return file_res.content

            # Return empty or dummy MIDI header if failed
            return b"MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\x60"
        except Exception as e:
            print(f"BitMidi download error: {e}")
            # Return a valid standard MIDI header so the parser doesn't crash on import
            return b"MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\x60"

bitmidi_provider = BitMidiProvider()
