"""Title/artist catalog search with fuzzy matching, autocomplete, and filters."""

from __future__ import annotations

import difflib
import re
from typing import List, Optional, Tuple

from sqlalchemy import or_, func, cast, String
from sqlalchemy.orm import Session

from app.models.song import Song
from app.services.discovery.serialize import song_skills, song_tempo, serialize_song


TEMPO_BUCKETS = {
    "slow": (0, 79),
    "medium": (80, 120),
    "fast": (121, 400),
}


def _normalize(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def fuzzy_score(query: str, title: str, artist: str) -> float:
    q = _normalize(query)
    t = _normalize(title)
    a = _normalize(artist)
    if not q:
        return 0.0
    score = 0.0
    if q == t:
        score += 80
    elif t.startswith(q):
        score += 55
    elif q in t:
        score += 40
    score += difflib.SequenceMatcher(None, q, t).ratio() * 30
    if q == a:
        score += 40
    elif a.startswith(q):
        score += 28
    elif q in a:
        score += 20
    score += difflib.SequenceMatcher(None, q, a).ratio() * 15
    return score


def _apply_filters(
    query,
    *,
    difficulty: Optional[str] = None,
    genre: Optional[str] = None,
    mood: Optional[str] = None,
    tempo: Optional[str] = None,
    language: Optional[str] = None,
    skill: Optional[str] = None,
):
    if difficulty:
        query = query.filter(Song.difficulty.ilike(difficulty.strip()))
    if genre:
        query = query.filter(Song.genre.ilike(f"%{genre.strip()}%"))
    if mood:
        query = query.filter(Song.mood.ilike(f"%{mood.strip()}%"))
    if language:
        query = query.filter(Song.language.ilike(f"%{language.strip()}%"))
    if skill:
        query = query.filter(cast(Song.skills, String).ilike(f"%{skill.strip()}%"))
    if tempo:
        low, high = _parse_tempo(tempo)
        if low is not None:
            tempo_expr = func.coalesce(Song.tempo, Song.bpm)
            query = query.filter(tempo_expr >= low, tempo_expr <= high)
    return query


def _parse_tempo(tempo: str) -> Tuple[Optional[int], Optional[int]]:
    raw = tempo.strip().lower()
    if raw in TEMPO_BUCKETS:
        return TEMPO_BUCKETS[raw]
    match = re.match(r"^(\d+)\s*-\s*(\d+)$", raw)
    if match:
        return int(match.group(1)), int(match.group(2))
    if raw.isdigit():
        value = int(raw)
        return max(0, value - 10), value + 10
    return None, None


def search_catalog(
    db: Session,
    *,
    q: Optional[str] = None,
    difficulty: Optional[str] = None,
    genre: Optional[str] = None,
    mood: Optional[str] = None,
    tempo: Optional[str] = None,
    language: Optional[str] = None,
    skill: Optional[str] = None,
    limit: int = 24,
    saved_ids: Optional[set] = None,
) -> List[dict]:
    query = db.query(Song)
    query = _apply_filters(
        query,
        difficulty=difficulty,
        genre=genre,
        mood=mood,
        tempo=tempo,
        language=language,
        skill=skill,
    )

    term = (q or "").strip()
    songs: List[Song]
    if term:
        like = f"%{term}%"
        candidates = query.filter(
            or_(
                Song.title.ilike(like),
                Song.artist.ilike(like),
                Song.composer.ilike(like),
                Song.album.ilike(like),
            )
        ).all()
        if len(candidates) < 8:
            extras = query.limit(200).all()
            seen = {s.id for s in candidates}
            for song in extras:
                if song.id in seen:
                    continue
                if fuzzy_score(term, song.title, song.artist or song.composer or "") >= 18:
                    candidates.append(song)
        ranked = sorted(
            candidates,
            key=lambda s: fuzzy_score(term, s.title, s.artist or s.composer or ""),
            reverse=True,
        )
        songs = ranked[:limit]
    else:
        songs = query.order_by(Song.title.asc()).limit(limit).all()

    saved_ids = saved_ids or set()
    results = []
    for song in songs:
        payload = serialize_song(song, saved=song.id in saved_ids)
        payload["rank_score"] = fuzzy_score(term, song.title, song.artist or song.composer or "") if term else 0.0
        results.append(payload)
    return results


def autocomplete_catalog(db: Session, q: str, limit: int = 8) -> List[dict]:
    term = (q or "").strip()
    if not term:
        return []
    like = f"{term}%"
    contains = f"%{term}%"
    songs = (
        db.query(Song)
        .filter(
            or_(
                Song.title.ilike(like),
                Song.artist.ilike(like),
                Song.title.ilike(contains),
                Song.artist.ilike(contains),
            )
        )
        .limit(40)
        .all()
    )
    ranked = sorted(
        songs,
        key=lambda s: fuzzy_score(term, s.title, s.artist or s.composer or ""),
        reverse=True,
    )[:limit]
    return [
        {
            "id": song.id,
            "title": song.title,
            "artist": song.artist or song.composer,
            "artwork": song.artwork_url or song.thumbnail_url,
        }
        for song in ranked
    ]
