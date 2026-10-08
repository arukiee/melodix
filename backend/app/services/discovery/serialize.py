from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.discovery import SavedSong
from app.models.song import Song
from app.schemas.song import SongSchema


DEFAULT_ARRANGEMENTS = ["Easy", "Medium", "Hard"]


def song_tempo(song: Song) -> Optional[int]:
    return song.tempo or song.bpm


def song_artwork(song: Song) -> Optional[str]:
    return song.artwork_url or song.thumbnail_url


def song_skills(song: Song) -> List[str]:
    skills = list(song.skills or [])
    if not skills:
        skills = list(song.skills_required or [])
    return skills


def learnable_status(song: Song) -> str:
    if song.is_learnable is False:
        return "unavailable"
    arrangements = song.available_arrangements or []
    if arrangements or song.source_type or song.file_url:
        return "learnable"
    return "processing"


def serialize_song(
    song: Song,
    *,
    saved: bool = False,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    tempo = song_tempo(song)
    artwork = song_artwork(song)
    skills = song_skills(song)
    arrangements = song.available_arrangements or list(DEFAULT_ARRANGEMENTS)
    payload = SongSchema.model_validate(song).model_dump()
    payload.update(
        {
            "tempo": tempo,
            "bpm": tempo or song.bpm,
            "key": song.key_signature,
            "artwork": artwork,
            "artwork_url": artwork,
            "thumbnail_url": artwork,
            "skills": skills,
            "available_arrangements": arrangements,
            "is_learnable": song.is_learnable is not False,
            "learnable_status": learnable_status(song),
            "saved": saved,
            "reason": reason,
        }
    )
    return payload


def saved_song_ids(db: Session, user_id: UUID) -> set:
    rows = db.query(SavedSong.song_id).filter(SavedSong.user_id == user_id).all()
    return {row[0] for row in rows}


def serialize_many(
    songs: Iterable[Song],
    *,
    saved_ids: Optional[set] = None,
    reasons: Optional[Dict[Any, str]] = None,
) -> List[Dict[str, Any]]:
    saved_ids = saved_ids or set()
    reasons = reasons or {}
    results = []
    for song in songs:
        results.append(
            serialize_song(
                song,
                saved=song.id in saved_ids,
                reason=reasons.get(song.id),
            )
        )
    return results
