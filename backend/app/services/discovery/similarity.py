from __future__ import annotations

import math
from typing import Iterable, List, Optional, Sequence


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right:
        return 0.0
    n = min(len(left), len(right))
    dot = 0.0
    left_norm = 0.0
    right_norm = 0.0
    for i in range(n):
        a = float(left[i])
        b = float(right[i])
        dot += a * b
        left_norm += a * a
        right_norm += b * b
    if left_norm <= 0 or right_norm <= 0:
        return 0.0
    return dot / math.sqrt(left_norm * right_norm)


def catalog_document(song) -> str:
    skills = " ".join(song.skills or song.skills_required or [])
    tempo = song.tempo or song.bpm
    tempo_word = "slow" if (tempo or 0) < 80 else "fast" if (tempo or 0) > 120 else "medium tempo"
    parts = [
        song.title or "",
        f"by {song.artist or song.composer or ''}",
        song.album or "",
        song.genre or "",
        song.mood or "",
        song.language or "",
        song.difficulty or "",
        song.key_signature or "",
        skills,
        tempo_word,
        f"{tempo or ''} bpm",
        " ".join(song.available_arrangements or []),
        "learnable" if song.is_learnable is not False else "",
    ]
    return " ".join(part for part in parts if part).strip()


def lexical_similarity(query: str, document: str) -> float:
    q_tokens = set(_tokenize(query))
    d_tokens = set(_tokenize(document))
    if not q_tokens or not d_tokens:
        return 0.0
    overlap = len(q_tokens & d_tokens) / len(q_tokens)
    like_bonus = 0.0
    lowered = document.lower()
    for token in q_tokens:
        if token in lowered:
            like_bonus += 0.08
    return overlap + like_bonus


def _tokenize(text: str) -> List[str]:
    stop = {
        "a", "an", "the", "for", "to", "of", "and", "or", "in", "on",
        "songs", "song", "like", "with", "piano",
    }
    tokens = []
    for raw in (text or "").lower().replace("-", " ").split():
        token = "".join(ch for ch in raw if ch.isalnum())
        if token and token not in stop:
            tokens.append(token)
    return tokens
