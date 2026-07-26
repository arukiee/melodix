"""Shared Pydantic schemas used across the API."""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List

T = TypeVar("T")

class IDResponse(BaseModel):
    id: int = Field(..., description="Database primary key identifier")

class Pagination(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    total: int = Field(..., description="Total number of items")

class PaginatedResponse(BaseModel, Generic[T]):
    pagination: Pagination
    items: List[T]

class ErrorResponse(BaseModel):
    detail: str
    code: int | None = None

class TimestampMixin(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SuccessResponse(BaseModel):
    success: bool = True
    message: str | None = None
