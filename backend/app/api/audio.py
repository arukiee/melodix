"""
Audio upload and management API.

Endpoints:
  POST /api/v1/audio/upload  — Accept audio/MIDI file, validate, store in MinIO, create ProcessingJob
  GET  /api/v1/audio/{id}    — Get audio asset metadata
"""

import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.audio_asset import AudioAsset
from app.models.processing_job import ProcessingJob
from app.core.enums import AudioSourceType, ProcessingJobStage
from app.schemas.pipeline import AudioUploadResponse, AudioAssetSchema

router = APIRouter(prefix="/api/v1/audio", tags=["Audio"])

# Supported audio formats for piano transcription (V1: piano-only)
SUPPORTED_FORMATS = {
    "wav", "mp3", "flac", "ogg", "m4a",  # audio
    "mid", "midi",                          # MIDI
}

# Magic byte signatures for format validation
FORMAT_SIGNATURES = {
    b"RIFF": "wav",
    b"\xff\xfb": "mp3",
    b"\xff\xf3": "mp3",
    b"\xff\xf2": "mp3",
    b"ID3": "mp3",
    b"fLaC": "flac",
    b"OggS": "ogg",
    b"MThd": "mid",
}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MIN_FILE_SIZE = 1024               # 1 KB


def _detect_format_from_bytes(header: bytes) -> str | None:
    """Detect audio format from file magic bytes."""
    for signature, fmt in FORMAT_SIGNATURES.items():
        if header.startswith(signature):
            return fmt
    # M4A/AAC check (ftyp box)
    if len(header) >= 8 and header[4:8] == b"ftyp":
        return "m4a"
    return None


def _get_extension(filename: str) -> str:
    """Extract lowercase file extension."""
    if "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return ""


@router.post(
    "/upload",
    response_model=AudioUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload audio file for transcription",
    description=(
        "Upload a piano audio file (WAV, MP3, FLAC, OGG, M4A) or MIDI file. "
        "The file is validated, stored in MinIO, and a processing pipeline job is created. "
        "V1 scope: piano-only recordings."
    ),
)
async def upload_audio(
    file: UploadFile = File(..., description="Audio or MIDI file to process"),
    song_id: Optional[str] = Form(None, description="Optional ID of the song to attach this source to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accept an audio/MIDI upload and start the Melodix processing pipeline.

    Flow:
    1. Read and validate file (size, format via magic bytes)
    2. Compute SHA-256 hash (deduplication + provenance)
    3. Store original file in MinIO: audio/{asset_id}/original.{ext}
    4. Create AudioAsset record
    5. Create ProcessingJob record (status=QUEUED)
    6. Dispatch Celery pipeline task
    7. Return 202 Accepted with job ID for polling
    """
    # ── 1. Read file content ──────────────────────────────────────────────
    content = await file.read()
    file_size = len(content)

    if file_size < MIN_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too small ({file_size} bytes). Minimum is {MIN_FILE_SIZE} bytes.",
        )
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large ({file_size} bytes). Maximum is {MAX_FILE_SIZE} bytes.",
        )

    # ── 2. Format detection via magic bytes ───────────────────────────────
    header = content[:16]
    detected_format = _detect_format_from_bytes(header)
    extension = _get_extension(file.filename or "unknown")

    # Use magic bytes if available, fall back to extension
    audio_format = detected_format or extension

    if audio_format not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported format: '{audio_format}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_FORMATS))}. "
                "V1 supports piano audio and MIDI files only."
            ),
        )

    # ── 3. Compute SHA-256 hash ───────────────────────────────────────────
    file_hash = hashlib.sha256(content).hexdigest()

    # Check for duplicate uploads
    existing = db.query(AudioAsset).filter(
        AudioAsset.file_hash_sha256 == file_hash,
        AudioAsset.user_id == current_user.id,
    ).first()

    if existing:
        # Return existing asset's processing job instead of re-uploading
        existing_job = db.query(ProcessingJob).filter(
            ProcessingJob.audio_asset_id == existing.id,
        ).order_by(ProcessingJob.created_at.desc()).first()

        if existing_job:
            return AudioUploadResponse(
                audio_asset_id=existing.id,
                processing_job_id=existing_job.id,
                original_filename=existing.original_filename,
                file_hash_sha256=existing.file_hash_sha256,
                file_size_bytes=existing.file_size_bytes,
                format=existing.format,
                message="File already uploaded. Returning existing processing job.",
            )

    # ── 4. Create AudioAsset record ───────────────────────────────────────
    asset_id = uuid.uuid4()
    storage_path = f"audio/{asset_id}/original.{audio_format}"

    audio_asset = AudioAsset(
        id=asset_id,
        user_id=current_user.id,
        source_type=AudioSourceType.USER_UPLOAD.value,
        original_filename=file.filename or "unknown",
        file_hash_sha256=file_hash,
        storage_path=storage_path,
        format=audio_format,
        file_size_bytes=file_size,
        is_valid=False,  # Will be set to True after validation stage
    )
    if song_id:
        try:
            audio_asset.song_id = uuid.UUID(song_id)
        except ValueError:
            pass
            
    db.add(audio_asset)

    # ── 5. Store in MinIO ─────────────────────────────────────────────────
    try:
        from app.storage.minio_service import minio_service
        minio_service.upload_bytes(storage_path, content, content_type=file.content_type or "application/octet-stream")
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store file: {str(e)}",
        )

    # ── 6. Create ProcessingJob ───────────────────────────────────────────
    job_id = uuid.uuid4()
    processing_job = ProcessingJob(
        id=job_id,
        audio_asset_id=asset_id,
        user_id=current_user.id,
        status=ProcessingJobStage.QUEUED.value,
        progress_percent=0,
        pipeline_version="1.0.0",
        stage_log=[],
    )
    if song_id:
        try:
            processing_job.song_id = uuid.UUID(song_id)
        except ValueError:
            pass
            
    db.add(processing_job)
    db.commit()

    # ── 7. Dispatch Celery pipeline task ──────────────────────────────────
    try:
        from app.tasks.transcribe_audio import process_audio_pipeline
        process_audio_pipeline.delay(str(job_id))
    except Exception:
        # If Celery is unavailable, job stays QUEUED for retry
        pass

    return AudioUploadResponse(
        audio_asset_id=asset_id,
        processing_job_id=job_id,
        original_filename=file.filename or "unknown",
        file_hash_sha256=file_hash,
        file_size_bytes=file_size,
        format=audio_format,
        message="Upload successful. Processing started.",
    )


@router.get(
    "/{audio_asset_id}",
    response_model=AudioAssetSchema,
    summary="Get audio asset metadata",
)
async def get_audio_asset(
    audio_asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve metadata for an uploaded audio asset."""
    asset = db.query(AudioAsset).filter(
        AudioAsset.id == audio_asset_id,
        AudioAsset.user_id == current_user.id,
    ).first()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio asset not found.",
        )

    return asset
