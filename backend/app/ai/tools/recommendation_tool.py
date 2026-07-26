from .base import Tool

class RecommendationTool(Tool):
    name = "recommendation"
    description = "Generate song recommendations"
    input_schema = {"type": "object", "properties": {"user_id": {"type": "string"}}}
    output_schema = {"type": "array", "items": {"type": "string"}}
    permissions = ["read:recommendation"]

    async def run(self, user_id: str):
        return ["song1", "song2"]
