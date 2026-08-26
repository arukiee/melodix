import asyncio
import json
import httpx
import re
from typing import List, Optional
from app.services.search.base_provider import BaseSearchProvider
from app.schemas.search import SearchResult, SearchFilter


def resolve_search_limit(filters: Optional[SearchFilter] = None, *, default: int = 10, minimum: int = 7, maximum: int = 10) -> int:
    requested_limit = getattr(filters, 'limit', None)
    if requested_limit is None:
        return default

    try:
        limit = int(requested_limit)
    except (TypeError, ValueError):
        return default

    if limit < minimum:
        return minimum
    if limit > maximum:
        return maximum
    return limit


def parse_duration_to_seconds(duration_str: str) -> int:
    """Converts a duration string like '3:45' or '1:02:15' to seconds."""
    if not duration_str:
        return 0
    try:
        parts = list(map(int, duration_str.split(':')))
        if len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except Exception:
        pass
    return 0


def parse_views_to_int(views_str: str) -> int:
    """Extracts numeric views from strings like '1,234,567 views' or '5.2K views'."""
    if not views_str:
        return 0
    try:
        # Strip non-digit characters except period and suffix letters
        views_str = views_str.lower().replace(',', '')
        match = re.search(r'([0-9.]+)\s*([kmb]?)', views_str)
        if match:
            num = float(match.group(1))
            suffix = match.group(2)
            if suffix == 'k':
                return int(num * 1000)
            elif suffix == 'm':
                return int(num * 1000000)
            elif suffix == 'b':
                return int(num * 1000000000)
            return int(num)
    except Exception:
        pass
    return 0


class YouTubeProvider(BaseSearchProvider):
    @property
    def provider_name(self) -> str:
        return "YouTube"
        
    async def search(self, query: str, filters: Optional[SearchFilter] = None, **kwargs) -> List[SearchResult]:
        limit = resolve_search_limit(filters)
        
        # Method 1: Fast direct HTTP scrape of youtube.com/results
        scraped_results = await self._search_via_scrape(query, limit)
        if scraped_results:
            return scraped_results
            
        # Method 2: Fallback to yt-dlp if scrape returns empty (e.g. captcha/structure change)
        return await self._search_via_ytdlp(query, limit)

    async def _search_via_scrape(self, query: str, limit: int) -> List[SearchResult]:
        try:
            url = f"https://www.youtube.com/results?search_query={query}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            }
            
            async with httpx.AsyncClient(follow_redirects=True, timeout=5.0) as client:
                res = await client.get(url, headers=headers)
                res.raise_for_status()

            # Find ytInitialData object in the page script
            match = re.search(r'ytInitialData\s*=\s*(\{.*?\});', res.text)
            if not match:
                # Try search for window["ytInitialData"] pattern
                match = re.search(r'window\["ytInitialData"\]\s*=\s*(\{.*?\});', res.text)

            if not match:
                return []

            data = json.loads(match.group(1))
            
            # Navigate nested structure of YouTube initial data response
            contents = data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])
            
            # Find the item section renderer containing the actual list of video results
            item_section = None
            for c in contents:
                if "itemSectionRenderer" in c:
                    item_section = c["itemSectionRenderer"]
                    break
            
            if not item_section:
                return []

            results = []
            for item in item_section.get("contents", []):
                if len(results) >= limit:
                    break

                if "videoRenderer" not in item:
                    continue
                    
                video = item["videoRenderer"]
                video_id = video.get("videoId")
                if not video_id:
                    continue

                # Extract title, uploader/channel name, duration, views, and thumbnail
                title = video.get("title", {}).get("runs", [{}])[0].get("text", "Unknown Title")
                uploader = video.get("ownerText", {}).get("runs", [{}])[0].get("text", "Unknown Artist")
                
                duration_str = video.get("lengthText", {}).get("simpleText", "")
                duration_secs = parse_duration_to_seconds(duration_str)
                
                views_str = video.get("viewCountText", {}).get("simpleText", "")
                views_count = parse_views_to_int(views_str)
                
                thumbnail_url = video.get("thumbnail", {}).get("thumbnails", [{}])[0].get("url", "")

                results.append(SearchResult(
                    id=video_id,
                    title=title,
                    artist=uploader,
                    provider=self.provider_name,
                    difficulty='Variable',
                    hasMidi=False,
                    hasChords=True,
                    hasSheetMusic=False,
                    duration=duration_secs,
                    popularity=views_count,
                    thumbnailUrl=thumbnail_url,
                    rank_score=0.0
                ))

            return results
        except Exception as e:
            print(f"Direct YouTube search scraping failed: {e}")
            return []

    async def _search_via_ytdlp(self, query: str, limit: int) -> List[SearchResult]:
        try:
            cmd = ['python3', '-m', 'yt_dlp', f'ytsearch{limit}:{query}', '--dump-json', '--no-warnings', '--flat-playlist']
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                print(f"yt-dlp error: {stderr.decode()}")
                return []
                
            results = []
            for line in stdout.decode().strip().split('\n'):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    results.append(SearchResult(
                        id=data.get('id', ''),
                        title=data.get('title', 'Unknown Title'),
                        artist=data.get('uploader', 'Unknown Artist'),
                        provider=self.provider_name,
                        difficulty='Variable',
                        hasMidi=False,
                        hasChords=True,
                        hasSheetMusic=False,
                        duration=data.get('duration', 0),
                        popularity=data.get('view_count', 0),
                        thumbnailUrl=data.get('thumbnails', [{'url': ''}])[0].get('url', ''),
                        rank_score=0.0
                    ))
                except Exception as e:
                    print(f"Failed to parse yt-dlp line: {e}")
            return results[:limit]
        except Exception as e:
            print(f"YouTube search fallback error: {e}")
            return []

    async def get_raw_data(self, item_id: str) -> bytes:
        """
        Uses yt-dlp to fetch the metadata of the YouTube video, and packs it as JSON bytes
        for the YouTubeImporter pipeline to analyze.
        """
        try:
            cmd = ['python3', '-m', 'yt_dlp', f'https://www.youtube.com/watch?v={item_id}', '--dump-json', '--no-warnings', '--flat-playlist']
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0 and stdout:
                data = json.loads(stdout.decode().strip().split('\n')[0])
                meta = {
                    "youtube_id": item_id,
                    "title": data.get('title', 'Unknown Title'),
                    "artist": data.get('uploader', 'Unknown Artist'),
                    "duration": data.get('duration', 180)
                }
                return json.dumps(meta).encode('utf-8')
        except Exception as e:
            print(f"YouTube metadata fetch error: {e}")
            
        # Fallback
        fallback = {
            "youtube_id": item_id,
            "title": "YouTube Song",
            "artist": "Unknown Artist",
            "duration": 180
        }
        return json.dumps(fallback).encode('utf-8')

youtube_provider = YouTubeProvider()
