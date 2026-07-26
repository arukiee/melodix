# backend/app/schemas/song_file.py
"""Pydantic schemas for SongFile.
Maps to the `SongFile` SQLAlchemy model.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from backend.app.models.songs import FileTypeEnum, StatusEnum, ProcessingStateEnum

class SongFileBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, orm_mode=True)
    id: int
    song_id: int
    file_type: FileTypeEnum
    uri: str
    is_primary: bool
    version: int
    status: StatusEnum
    processing_state: ProcessingStateEnum
    created_at: datetime
    updated_at: datetime

class SongFileCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, orm_mode=True)
    song_id: int
    file_type: FileTypeEnum
    uri: str
    is_primary: bool = False
    version: int = 1
    status: StatusEnum = StatusEnum.PENDING
    processing_state: ProcessingStateEnum = ProcessingStateEnum.NOT_STARTED

class SongFileUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, orm_mode=True)
    uri: Optional[str] = None
    is_primary: Optional[bool] = None
    version: Optional[int] = None
    status: Optional[StatusEnum] = None
    processing_state: Optional[ProcessingStateEnum] = None

class SongFileDetail(SongFileBase):
    """Complete representation of a song file, suitable for detail views."""
    pass
