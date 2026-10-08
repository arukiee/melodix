"""
Spotify API Client.

Provides token acquisition via Client Credentials flow and track search for accurate song metadata.
"""

import base64
import logging
from typing import Any, Dict, Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_spotify_token(client_id: Optional[str] = None, client_secret: Optional[str] = None) -> Optional[str]:
    """Obtain a Client Credentials access token from Spotify."""
    client_id = client_id or getattr(settings, "SPOTIFY_CLIENT_ID", None)
    client_secret = client_secret or getattr(settings, "SPOTIFY_CLIENT_SECRET", None)

    if not client_id or not client_secret:
        logger.debug("Spotify Client ID or Secret not configured.")
        return None

    auth_str = f"{client_id}:{client_secret}"
    auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

    try:
        resp = requests.post(
            "https://accounts.spotify.com/api/token",
            headers={"Authorization": f"Basic {auth_b64}"},
            data={"grant_type": "client_credentials"},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
        else:
            logger.warning(f"Spotify token request failed (HTTP {resp.status_code}): {resp.text}")
            return None
    except Exception as e:
        logger.error(f"Error fetching Spotify token: {e}")
        return None


def search_spotify_tracks(query: str, limit: int = 10, token: Optional[str] = None) -> list[dict[str, Any]]:
    """Search Spotify for multiple tracks and return structured metadata list."""
    if not token:
        token = get_spotify_token()
    if not token:
        return []

    try:
        resp = requests.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": query, "type": "track", "limit": limit},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.warning(f"Spotify search failed (HTTP {resp.status_code}): {resp.text}")
            return []

        items = resp.json().get("tracks", {}).get("items", [])
        results = []
        for track in items:
            artist_name = track["artists"][0]["name"] if track.get("artists") else "Unknown Artist"
            album_name = track.get("album", {}).get("name", "Unknown Album")
            images = track.get("album", {}).get("images", [])
            album_art_url = images[0].get("url") if images else None

            results.append({
                "title": track.get("name"),
                "artist": artist_name,
                "duration_ms": track.get("duration_ms", 0),
                "album": album_name,
                "album_art_url": album_art_url,
                "spotify_id": track.get("id"),
                "external_url": track.get("external_urls", {}).get("spotify"),
            })
        return results
    except Exception as e:
        logger.error(f"Error searching Spotify tracks for query '{query}': {e}")
        return []


def search_spotify_track(query: str, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Search Spotify for a single track and return structured metadata."""
    results = search_spotify_tracks(query, limit=1, token=token)
    return results[0] if results else None

