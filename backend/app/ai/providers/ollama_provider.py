"""Ollama LLM provider wrapper (local Ollama server)."""

import httpx
from .llm_provider import LLMProvider

class OllamaProvider(LLMProvider):
    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3"):
        self.host = host.rstrip('/')
        self.model = model

    async def generate(self, prompt: str, **kwargs) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.host}/api/generate",
                json={"model": self.model, "prompt": prompt, **kwargs},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")
