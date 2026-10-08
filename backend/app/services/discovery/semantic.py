from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.song import Song
from app.services.discovery.embeddings import OllamaEmbeddingProvider
from app.services.discovery.serialize import serialize_song
from app.services.discovery.similarity import catalog_document, cosine_similarity, lexical_similarity

logger = logging.getLogger("melodix.discovery.semantic")


def _is_postgres(db: Session) -> bool:
    return db.bind.dialect.name == "postgresql" if db.bind is not None else False


async def index_song_embedding(
    db: Session,
    song: Song,
    provider: Optional[OllamaEmbeddingProvider] = None,
) -> Optional[List[float]]:
    provider = provider or OllamaEmbeddingProvider()
    try:
        vector = await provider.embed(catalog_document(song))
    except Exception as exc:
        logger.info("Skipping embedding for %s: %s", song.title, exc)
        return None
    song.embedding = vector
    db.add(song)
    db.commit()
    db.refresh(song)
    return vector


async def index_missing_embeddings(
    db: Session,
    provider: Optional[OllamaEmbeddingProvider] = None,
    limit: int = 50,
) -> int:
    songs = db.query(Song).filter(Song.embedding.is_(None)).limit(limit).all()
    count = 0
    provider = provider or OllamaEmbeddingProvider()
    for song in songs:
        try:
            song.embedding = await provider.embed(catalog_document(song))
            db.add(song)
            count += 1
        except Exception as exc:
            logger.info("Could not embed %s: %s", song.title, exc)
            break
    if count:
        db.commit()
    return count


async def semantic_search(
    db: Session,
    query: str,
    *,
    saved_ids: Optional[set] = None,
    limit: int = 12,
    provider: Optional[OllamaEmbeddingProvider] = None,
) -> dict:
    saved_ids = saved_ids or set()
    provider = provider or OllamaEmbeddingProvider()
    mode = "lexical"
    query_vector: Optional[List[float]] = None
    try:
        query_vector = await provider.embed(query)
        mode = "ollama"
    except Exception as exc:
        logger.info("Semantic search falling back to lexical matching: %s", exc)

    songs: List[Song] = []
    scored: List[tuple] = []

    if query_vector and _is_postgres(db):
        try:
            vector_literal = "[" + ",".join(str(float(x)) for x in query_vector) + "]"
            rows = db.execute(
                text(
                    """
                    SELECT id
                    FROM songs
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> CAST(:vec AS vector)
                    LIMIT :limit
                    """
                ),
                {"vec": vector_literal, "limit": limit},
            ).fetchall()
            ids = [row[0] for row in rows]
            if ids:
                found = db.query(Song).filter(Song.id.in_(ids)).all()
                by_id = {song.id: song for song in found}
                songs = [by_id[song_id] for song_id in ids if song_id in by_id]
                for song in songs:
                    reason = _semantic_reason(query, song)
                    scored.append((song, 1.0, reason))
        except Exception as exc:
            logger.info("pgvector query unavailable, using in-memory cosine: %s", exc)

    if not scored:
        candidates = db.query(Song).all()
        for song in candidates:
            if query_vector and song.embedding:
                score = cosine_similarity(query_vector, song.embedding)
            else:
                score = lexical_similarity(query, catalog_document(song))
            if score <= 0:
                continue
            scored.append((song, score, _semantic_reason(query, song)))
        scored.sort(key=lambda item: item[1], reverse=True)
        scored = scored[:limit]

    results = [
        serialize_song(song, saved=song.id in saved_ids, reason=reason)
        for song, _score, reason in scored
    ]
    return {"query": query, "mode": mode, "results": results}


def _semantic_reason(query: str, song: Song) -> str:
    q = query.lower()
    bits = []
    if song.difficulty and song.difficulty.lower() in q:
        bits.append(f"it is {song.difficulty.lower()}")
    if song.mood and song.mood.lower() in q:
        bits.append(f"the mood is {song.mood.lower()}")
    if song.genre and song.genre.lower() in q:
        bits.append(f"you asked for {song.genre.lower()}")
    skills = song.skills or []
    for skill in skills:
        token = skill.replace("-", " ").lower()
        if token in q or skill.lower() in q:
            bits.append(f"it practices {token}")
            break
    if "like" in q and (song.title or "").lower() in q:
        bits.append(f"it is similar to {song.title}")
    if not bits:
        bits.append("it matches the meaning of your search")
    return "Recommended because " + " and ".join(bits) + "."
