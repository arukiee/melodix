"""Prompt model with optional variables."""

from pydantic import BaseModel

class Prompt(BaseModel):
    name: str
    version: str = "v1"
    template: str
    variables: dict = {}
