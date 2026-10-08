from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.discovery import (
    ClassMembership,
    ClassSongAssignment,
    SongLearningProgress,
)
from app.models.profile import Profile
from app.models.social import Friendship
from app.models.song import Song
from app.models.student_progress import StudentLearningState
from app.models.user import User
from app.services.discovery.serialize import serialize_song, song_skills


ROW_SPECS = [
    ("continue_learning", "Continue Learning"),
    ("made_for_your_level", "Made for Your Level"),
    ("weak_skill", "Recommended for Your Weak Skill"),
    ("trending_in_class", "Trending in Your Class"),
    ("friends_are_learning", "Friends Are Learning"),
    ("quick_wins", "Quick Wins Under 10 Minutes"),
]


def _weak_skill(state: Optional[StudentLearningState]) -> Optional[str]:
    if not state:
        return None
    if state.weak_areas:
        first = state.weak_areas[0]
        if isinstance(first, dict):
            return first.get("type") or first.get("skill")
        if isinstance(first, str):
            return first
    levels = state.skill_levels or {}
    if levels:
        return min(levels.items(), key=lambda item: item[1] or 0)[0]
    return None


def _level_aliases(profile: Optional[Profile], state: Optional[StudentLearningState]) -> List[str]:
    raw = (state.current_difficulty if state else None) or (profile.skill_level if profile else None) or "BEGINNER"
    raw = str(raw).upper()
    mapping = {
        "EASY": ["Beginner", "Easy"],
        "BEGINNER": ["Beginner", "Easy"],
        "MEDIUM": ["Intermediate", "Medium"],
        "INTERMEDIATE": ["Intermediate", "Medium"],
        "HARD": ["Advanced", "Hard"],
        "ADVANCED": ["Advanced", "Hard"],
    }
    return mapping.get(raw, ["Beginner", "Easy"])


def _favorite_genres(profile: Optional[Profile]) -> List[str]:
    if not profile:
        return []
    return [str(g) for g in (profile.preferred_genres or []) if g]


def recommendation_reason(
    song: Song,
    *,
    favorite_genres: List[str],
    weak_skill: Optional[str],
    row_id: str,
) -> str:
    liked = None
    song_genre = (song.genre or "").lower()
    for genre in favorite_genres:
        if genre and genre.lower() in song_genre:
            liked = genre.lower()
            break
    if not liked and favorite_genres:
        liked = favorite_genres[0].lower()
    if not liked and song.genre:
        liked = song.genre.lower()

    skill = weak_skill or (song_skills(song)[0] if song_skills(song) else "technique")
    skill_phrase = str(skill).replace("_", " ").replace("-", " ").lower()

    if row_id == "continue_learning":
        return f"Recommended because you already started this {liked or 'piece'} and can keep building {skill_phrase}."
    if row_id == "made_for_your_level":
        level = (song.difficulty or "your").lower()
        if liked:
            return f"Recommended because you like {liked} songs and this {level} arrangement fits your level."
        return f"Recommended because this {level} piece matches your current level."
    if row_id == "weak_skill":
        if liked:
            return f"Recommended because you like {liked} songs and need {skill_phrase} practice."
        return f"Recommended because you need {skill_phrase} practice."
    if row_id == "trending_in_class":
        return f"Recommended because classmates are learning this and it helps with {skill_phrase}."
    if row_id == "friends_are_learning":
        return f"Recommended because friends are learning this {liked or 'song'} and you can practice {skill_phrase} together."
    if row_id == "quick_wins":
        minutes = max(1, int((song.duration or 180) / 60))
        return f"Recommended because you can finish this in about {minutes} minutes and practice {skill_phrase}."
    if liked:
        return f"Recommended because you like {liked} songs and need {skill_phrase} practice."
    return f"Recommended because you need {skill_phrase} practice."


def _exclude(query, used: set):
    if used:
        return query.filter(~Song.id.in_(list(used)))
    return query


def build_home_rows(db: Session, user: User, *, saved_ids: Optional[set] = None) -> dict:
    saved_ids = saved_ids or set()
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    state = db.query(StudentLearningState).filter(StudentLearningState.user_id == user.id).first()
    favorite_genres = _favorite_genres(profile)
    weak = _weak_skill(state)
    levels = _level_aliases(profile, state)
    used: set = set()

    def pack(row_id: str, title: str, songs: List[Song]) -> dict:
        items = []
        for song in songs:
            used.add(song.id)
            reason = recommendation_reason(
                song,
                favorite_genres=favorite_genres,
                weak_skill=weak,
                row_id=row_id,
            )
            items.append(serialize_song(song, saved=song.id in saved_ids, reason=reason))
        return {"id": row_id, "title": title, "songs": items}

    continue_rows = (
        db.query(Song)
        .join(SongLearningProgress, SongLearningProgress.song_id == Song.id)
        .filter(
            SongLearningProgress.user_id == user.id,
            SongLearningProgress.completed.is_(False),
        )
        .order_by(SongLearningProgress.last_played_at.desc())
        .limit(8)
        .all()
    )

    level_query = _exclude(db.query(Song).filter(Song.difficulty.in_(levels), Song.is_learnable.is_not(False)), used)
    if favorite_genres:
        from sqlalchemy import or_
        level_query = level_query.filter(or_(*[Song.genre.ilike(f"%{g}%") for g in favorite_genres]))
    level_songs = level_query.order_by(Song.title.asc()).limit(8).all()
    if len(level_songs) < 4:
        extra = (
            _exclude(db.query(Song).filter(Song.difficulty.in_(levels)), used)
            .limit(8)
            .all()
        )
        seen = {s.id for s in level_songs}
        for song in extra:
            if song.id not in seen:
                level_songs.append(song)

    weak_songs: List[Song] = []
    if weak:
        from sqlalchemy import cast, String
        weak_songs = (
            _exclude(db.query(Song).filter(cast(Song.skills, String).ilike(f"%{weak}%")), used)
            .limit(8)
            .all()
        )
    if not weak_songs:
        weak_songs = _exclude(db.query(Song), used).limit(8).all()

    class_ids = [
        row[0]
        for row in db.query(ClassMembership.class_id).filter(ClassMembership.user_id == user.id).all()
    ]
    trending: List[Song] = []
    if class_ids:
        trending_ids = (
            db.query(ClassSongAssignment.song_id, func.count(ClassSongAssignment.id).label("n"))
            .filter(ClassSongAssignment.class_id.in_(class_ids))
            .group_by(ClassSongAssignment.song_id)
            .order_by(func.count(ClassSongAssignment.id).desc())
            .limit(8)
            .all()
        )
        ids = [row[0] for row in trending_ids if row[0] not in used]
        if ids:
            found = db.query(Song).filter(Song.id.in_(ids)).all()
            by_id = {s.id: s for s in found}
            trending = [by_id[i] for i in ids if i in by_id]
    if not trending:
        progress_ids = (
            db.query(SongLearningProgress.song_id, func.count(SongLearningProgress.id))
            .group_by(SongLearningProgress.song_id)
            .order_by(func.count(SongLearningProgress.id).desc())
            .limit(8)
            .all()
        )
        ids = [row[0] for row in progress_ids if row[0] not in used]
        if ids:
            found = db.query(Song).filter(Song.id.in_(ids)).all()
            by_id = {s.id: s for s in found}
            trending = [by_id[i] for i in ids if i in by_id]
    if not trending:
        trending = _exclude(db.query(Song), used).limit(8).all()

    friend_ids = [
        row[0]
        for row in db.query(Friendship.friend_id).filter(Friendship.user_id == user.id).all()
    ]
    friends_songs: List[Song] = []
    if friend_ids:
        friend_progress = (
            db.query(SongLearningProgress.song_id)
            .filter(SongLearningProgress.user_id.in_(friend_ids))
            .order_by(SongLearningProgress.last_played_at.desc())
            .limit(16)
            .all()
        )
        ids = []
        for row in friend_progress:
            if row[0] not in used and row[0] not in ids:
                ids.append(row[0])
        if ids:
            found = db.query(Song).filter(Song.id.in_(ids)).all()
            by_id = {s.id: s for s in found}
            friends_songs = [by_id[i] for i in ids if i in by_id][:8]
    if not friends_songs:
        friends_songs = _exclude(db.query(Song), used).limit(8).all()

    quick = (
        _exclude(
            db.query(Song).filter(
                Song.duration.is_not(None),
                Song.duration <= 600,
                Song.is_learnable.is_not(False),
            ),
            used,
        )
        .order_by(Song.duration.asc())
        .limit(8)
        .all()
    )

    rows = [
        pack("continue_learning", "Continue Learning", continue_rows),
        pack("made_for_your_level", "Made for Your Level", level_songs[:8]),
        pack("weak_skill", "Recommended for Your Weak Skill", weak_songs[:8]),
        pack("trending_in_class", "Trending in Your Class", trending[:8]),
        pack("friends_are_learning", "Friends Are Learning", friends_songs[:8]),
        pack("quick_wins", "Quick Wins Under 10 Minutes", quick[:8]),
    ]
    return {"rows": rows}
