import json
import logging
from pydantic import BaseModel
from typing import List, Dict, Any

from app.services.ai_coach.ollama import generate_ollama_completion
from app.services.music_engine.base_analyzer import ScoreBreakdown, TempoMetrics, AnalysisMistake

logger = logging.getLogger("melodix.ai_coach.service")

class AICoachFeedback(BaseModel):
    summary: str
    strengths: List[str]
    improvements: List[str]
    nextGoal: str
    recommend_loop_measure: int | None = None
    recommend_tempo_change: int = 0

class AICoachingService:
    @staticmethod
    async def generate_coaching(
        song_title: str,
        scores: ScoreBreakdown,
        tempo_metrics: TempoMetrics,
        mistakes: List[AnalysisMistake],
        measure_scores: Dict[int, float] = {}
    ) -> AICoachFeedback:
        """
        Creates prompt template using performance scoring data, submits to local Ollama,
        and parses structured teacher coaching.
        """
        mistakes_summary = "\n".join([f"- At {m.timestamp:.1f}s: {m.details}" for m in mistakes])
        measures_summary = "\n".join([f"- Measure {m_idx + 1}: Score {m_score:.1f}%" for m_idx, m_score in measure_scores.items()])
        
        prompt = f"""
You are a friendly, encouraging piano teacher. Analyze this student's piano performance and provide constructive, teacher-like coaching.
Return your output ONLY as a JSON object with this exact structure:
{{
  "summary": "Short 1-2 sentence overall encouraging summary.",
  "strengths": ["Strength point 1", "Strength point 2"],
  "improvements": ["Improvement point 1", "Improvement point 2"],
  "nextGoal": "One concrete practice instruction for their next attempt.",
  "recommend_loop_measure": null,
  "recommend_tempo_change": 0
}}

Notes for JSON schema:
- recommend_loop_measure: integer (e.g. 8) if a specific measure had many mistakes and should be looped, otherwise null.
- recommend_tempo_change: integer. -10 to slow down if overall score is < 80, 0 to keep the same, +10 if score > 95.

Performance Metadata:
- Piece: {song_title}
- Target BPM: {tempo_metrics.targetBpm}
- Average BPM: {tempo_metrics.averageBpm:.1f}
- Tempo Stability Score: {tempo_metrics.stabilityScore:.1f}%

Performance Scores:
- Pitch Accuracy: {scores.pitchScore}%
- Rhythm Accuracy: {scores.rhythmScore}%
- Tempo Stability: {scores.tempoScore}%
- Overall Evaluation: {scores.overallScore}%

Measure-by-Measure Performance:
{measures_summary}

Timing & Pitch Mistakes list:
{mistakes_summary}
Remember:
1. Praise their effort and state strengths first.
2. Address weaknesses objectively.
3. Suggest 2-3 specific exercises (e.g. slowing down tempo, playing one hand at a time).
4. Refer to specific measures in your feedback where scores are low or mistakes occur.
5. Provide a recommendation for `recommend_loop_measure` and `recommend_tempo_change` based on the scores.
"""


        response_txt = await generate_ollama_completion(prompt)
        
        # Fallback response if Ollama is unavailable
        fallback = AICoachFeedback(
            summary=f"Great attempt on {song_title}! Your overall stability was {tempo_metrics.stabilityScore:.1f}%. Keep practicing to smooth out transitions.",
            strengths=["Strong overall note accuracy.", "Consistent hand positioning."],
            improvements=["Rhythm drifted slightly during timing changes.", "A few notes were held past their expected duration."],
            nextGoal=f"Try practicing at {tempo_metrics.targetBpm - 5} BPM with a metronome to reinforce timing before speeding up.",
            recommend_loop_measure=None,
            recommend_tempo_change=-5 if scores.overallScore < 85 else 0
        )

        if not response_txt:
            return fallback

        try:
            parsed = json.loads(response_txt)
            return AICoachFeedback(
                summary=parsed.get("summary", fallback.summary),
                strengths=parsed.get("strengths", fallback.strengths),
                improvements=parsed.get("improvements", fallback.improvements),
                nextGoal=parsed.get("nextGoal", fallback.nextGoal),
                recommend_loop_measure=parsed.get("recommend_loop_measure"),
                recommend_tempo_change=parsed.get("recommend_tempo_change", 0)
            )
        except Exception as e:
            logger.error(f"Failed to parse Ollama JSON feedback response: {str(e)}")
            return fallback
