"""
Orchestrator — Routes user intent to deterministic services.
"""

import logging

logger = logging.getLogger(__name__)


class UserIntent:
    def __init__(self, action: str, query: str = None, params: dict = None):
        self.action = action
        self.query = query
        self.params = params or {}


class MelodixOrchestrator:
    """
    Routes user intent to deterministic services and ML models.
    Does NOT hallucinate answers. Does NOT generate musical data.
    Sits ABOVE the pipeline — decides what executes next.
    """
    
    async def handle_intent(self, intent: UserIntent) -> dict:
        """Handle a user intent."""
        logger.info(f"Orchestrator handling intent: {intent.action}")
        
        match intent.action:
            case "search_song":
                return {"status": "routed_to_search", "query": intent.query}
            case "learn_song":
                return await self._learn_song_pipeline(intent)
            case "practice":
                return {"status": "routed_to_practice_evaluation"}
            case _:
                return {"status": "unknown_intent"}

    async def _learn_song_pipeline(self, intent: UserIntent) -> dict:
        """
        1. Search → 2. Resolve → 3. Check audio source
        → 4. Create ProcessingJob → 5. Dispatch Celery
        """
        # Placeholder for full orchestration flow
        return {
            "status": "learning_pipeline_started",
            "message": "Intent routed to song learning pipeline."
        }
