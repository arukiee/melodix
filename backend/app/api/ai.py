from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import httpx
import logging

from ..core.config import settings
from ..api.deps import get_current_user
from ..models.user import User

router = APIRouter(prefix="/ai", tags=["ai"])

class AICoachRequest(BaseModel):
    song_title: Optional[str] = "Clair de Lune"
    accuracy: float = 90.0
    rhythm_score: float = 85.0
    difficulty: Optional[str] = "Intermediate"

class AICoachResponse(BaseModel):
    status: str
    advice: str
    goal: str
    mistakes: List[str]
    accuracy: float
    rhythm_score: float
    tempo_stability: float
    expression_score: float

@router.post("/coach", response_model=AICoachResponse)
async def generate_ai_coaching(
    request: AICoachRequest,
    current_user: User = Depends(get_current_user)
):
    prompt = (
        f"You are Melodix AI Piano Coach. A student played '{request.song_title}' ({request.difficulty}) "
        f"with {request.accuracy}% pitch accuracy and {request.rhythm_score}% rhythm score. "
        f"Give 2 concise sentences of supportive, actionable advice on timing, phrasing, and dynamic control."
    )

    advice_text = ""
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.post(
                f"{settings.OLLAMA_HOST}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False
                }
            )
            if resp.status_code == 200:
                advice_text = resp.json().get("response", "").strip()
    except Exception as exc:
        logging.info("Ollama LLM connection fallback: %s", exc)

    if not advice_text:
        # Fallback intelligent feedback when LLM is initializing
        if request.rhythm_score < 90:
            advice_text = f"Great effort on '{request.song_title}'! Focus on keeping a steady pulse through complex measures and practice at 80% tempo using a metronome."
        else:
            advice_text = f"Excellent performance on '{request.song_title}'! Your pitch precision and rhythm control are sharp. Focus next on dynamic expression and legato phrasing."

    mistakes = []
    if request.rhythm_score < 90:
        mistakes.append("Slight rhythm acceleration in complex measures")
    if request.accuracy < 92:
        mistakes.append("Minor pitch slips during transition passages")
    if not mistakes:
        mistakes.append("Minor tempo fluctuation on cadential resolution")

    return {
        "status": "success",
        "advice": advice_text,
        "goal": f"Master steady rhythm & dynamic expression in {request.song_title}",
        "mistakes": mistakes,
        "accuracy": request.accuracy,
        "rhythm_score": request.rhythm_score,
        "tempo_stability": round((request.rhythm_score + request.accuracy) / 2, 1),
        "expression_score": round(min(98.0, request.accuracy + 2), 1)
    }
