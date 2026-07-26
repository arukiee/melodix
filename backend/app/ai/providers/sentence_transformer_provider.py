"""Sentence‑Transformer based embedding provider (local model)."""

from .embedding_provider import EmbeddingProvider

class SentenceTransformerProvider(EmbeddingProvider):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    async def embed(self, text: str) -> list[float]:
        # In a real async env you would run this in a thread pool
        return self.model.encode([text])[0].tolist()
