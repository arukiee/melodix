from .base import Tool

class SongTool(Tool):
    name = "song"
    description = "Operations related to songs"
    input_schema = {"type": "object", "properties": {"song_id": {"type": "string"}}}
    output_schema = {"type": "object", "properties": {"title": {"type": "string"}}}
    permissions = ["read:song"]

    async def run(self, song_id: str):
        return {"title": f"Song {song_id}"}
