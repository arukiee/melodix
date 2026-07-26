"""Tool definition schema for registration."""

from pydantic import BaseModel

class ToolSpec(BaseModel):
    name: str
    description: str
    input_schema: dict
    output_schema: dict
    permissions: list[str]
