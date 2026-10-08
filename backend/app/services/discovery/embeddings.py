"""Ollama embedding client used by song discovery semantic search."""

from __future__ import annotations

import logging
from typing import List, Optional

import httpx

from app.ai.providers.embedding_provider import EmbeddingProvider
from app.core.config import settings

logger = logging.getLogger("melodix.discovery.embeddings")


class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 20.0,
    ):
        self.host = (host or settings.OLLAMA_HOST or "http://localhost:11434").rstrip("/")
        self.model = model or settings.OLLAMA_EMBED_MODEL
        self.timeout = timeout

    async def embed(self, text: str) -> List[float]:
        vectors = await self.embed_many([text])
        return vectors[0]

    async def embed_many(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            vectors: List[List[float]] = []
            for text in texts:
                payload = {"model": self.model, "input": text}
                try:
                    resp = await client.post(f"{self.host}/api/embed", json=payload)
                    if resp.status_code == 404:
                        resp = await client.post(
                            f"{self.host}/api/embeddings",
                            json={"model": self.model, "prompt": text},
                        )
                    resp.raise_for_status()
                    data = resp.json()
                    vector = _extract_vector(data)
                    if not vector:
                        raise ValueError("Ollama returned an empty embedding")
                    vectors.append(vector)
                except Exception as exc:
                    logger.warning("Ollama embed failed: %s", exc)
                    raise
            return vectors


def _extract_vector(data: dict) -> List[float]:
    if "embeddings" in data and data["embeddings"]:
        first = data["embeddings"][0]
        if isinstance(first, list):
            return first
    if "embedding" in data and isinstance(data["embedding"], list):
        return data["embedding"]
    return []
