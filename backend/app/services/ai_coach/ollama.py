import httpx
import logging
from app.core.config import settings

logger = logging.getLogger("melodix.ai_coach.ollama")

async def generate_ollama_completion(prompt: str) -> str:
    """Sends a chat request to the local Ollama LLM provider."""
    # Fallback host if settings not loaded
    ollama_host = settings.OLLAMA_HOST or "http://localhost:11434"
    url = f"{ollama_host}/api/generate"
    
    payload = {
        "model": "llama3",  # default local llama3 model
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", "")
            else:
                logger.error(f"Ollama returned error status: {resp.status_code}")
                return ""
    except Exception as e:
        logger.error(f"Failed to communicate with local Ollama: {str(e)}")
        return ""
