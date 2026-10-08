"""
Processing pipeline status API.

Endpoints:
  GET /api/v1/pipeline/{job_id}           — Get ProcessingJob status, stage, progress
  GET /api/v1/pipeline/{job_id}/artifacts — List MinIO artifact paths
  GET /api/v1/pipeline/user/jobs          — List current user's processing jobs
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.processing_job import ProcessingJob
from app.models.transcription import Transcription
from app.models.provenance import ProcessingProvenance
from app.schemas.pipeline import (
    ProcessingJobStatus,
    ProcessingJobSummary,
    PipelineArtifactsResponse,
    TranscriptionNotesResponse,
    CanonicalNote,
)

router = APIRouter(prefix="/api/v1/pipeline", tags=["Pipeline"])


@router.get(
    "/{job_id}",
    response_model=ProcessingJobStatus,
    summary="Get processing pipeline status",
    description=(
        "Poll this endpoint to track the progress of an audio processing job. "
        "Returns the current stage, progress percentage, and any error information."
    ),
)
async def get_pipeline_status(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the current status of a processing pipeline job.
    The frontend polls this to show real progress through stages:
    QUEUED → VALIDATING → TRANSCRIBING → VALIDATING_NOTES → ...  → COMPLETED
    """
    job = db.query(ProcessingJob).filter(
        ProcessingJob.id == job_id,
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found.",
        )

    # If completed, include transcription summary data
    transcription_id = None
    note_count = None
    tempo_bpm = None
    tempo_confidence = None

    if job.transcription:
        transcription_id = job.transcription.id
        note_count = job.transcription.note_count

    if job.provenance:
        tempo_bpm = job.provenance.tempo_value
        tempo_confidence = job.provenance.tempo_confidence

    return ProcessingJobStatus(
        id=job.id,
        audio_asset_id=job.audio_asset_id,
        song_id=job.song_id,
        status=job.status,
        progress_percent=job.progress_percent,
        pipeline_version=job.pipeline_version,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_code=job.error_code,
        error_message=job.error_message,
        stage_log=job.stage_log or [],
        created_at=job.created_at,
        transcription_id=transcription_id,
        note_count=note_count,
        tempo_bpm=tempo_bpm,
        tempo_confidence=tempo_confidence,
    )


@router.get(
    "/user/jobs",
    response_model=List[ProcessingJobSummary],
    summary="List user's processing jobs",
)
async def list_user_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all processing jobs for the current user, most recent first."""
    jobs = db.query(ProcessingJob).filter(
        ProcessingJob.user_id == current_user.id,
    ).order_by(ProcessingJob.created_at.desc()).limit(50).all()

    return [
        ProcessingJobSummary(
            id=j.id,
            status=j.status,
            progress_percent=j.progress_percent,
            pipeline_version=j.pipeline_version,
            created_at=j.created_at,
        )
        for j in jobs
    ]


@router.get(
    "/{job_id}/artifacts",
    response_model=PipelineArtifactsResponse,
    summary="List pipeline artifacts",
    description="Returns MinIO paths to all raw artifacts preserved during processing.",
)
async def get_pipeline_artifacts(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all preserved artifacts for a processing job.
    This enables full data provenance — every artifact is traceable.
    """
    job = db.query(ProcessingJob).filter(
        ProcessingJob.id == job_id,
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found.",
        )

    audio_artifacts = {}
    transcription_artifacts = {}
    analysis_artifacts = {}

    # Audio artifacts
    if job.audio_asset:
        audio_artifacts["original"] = job.audio_asset.storage_path
        audio_artifacts["metadata"] = f"audio/{job.audio_asset_id}/metadata.json"

    # Transcription artifacts
    if job.transcription:
        t = job.transcription
        if t.raw_midi_path:
            transcription_artifacts["raw_midi"] = t.raw_midi_path
        if t.model_output_path:
            transcription_artifacts["model_output"] = t.model_output_path
        if t.note_events_path:
            transcription_artifacts["note_events"] = t.note_events_path

    # Analysis artifacts from provenance
    if job.provenance and job.provenance.artifact_paths:
        analysis_artifacts = job.provenance.artifact_paths

    return PipelineArtifactsResponse(
        processing_job_id=job_id,
        audio_artifacts=audio_artifacts,
        transcription_artifacts=transcription_artifacts,
        analysis_artifacts=analysis_artifacts,
    )


@router.get(
    "/{job_id}/notes",
    response_model=TranscriptionNotesResponse,
    summary="Get transcription notes",
    description="Returns all validated notes in canonical Melodix format.",
)
async def get_transcription_notes(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the canonical note data from a completed transcription.
    Only returns validated notes (validation_action != DISCARD).
    """
    job = db.query(ProcessingJob).filter(
        ProcessingJob.id == job_id,
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found.",
        )

    if not job.transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not yet available. Check pipeline status.",
        )

    t = job.transcription

    # Filter out discarded notes — keep everything else (KEEP, MERGE, FLAG, unvalidated)
    valid_notes = [
        n for n in t.notes
        if n.validation_action != "DISCARD"
    ]

    notes = [
        CanonicalNote(
            id=n.id,
            sequence_index=n.sequence_index,
            midi_number=n.midi_number,
            note_name=n.note_name,
            start_time=n.start_time,
            end_time=n.end_time,
            duration=n.duration,
            velocity=n.velocity,
            confidence=n.confidence,
            is_validated=n.is_validated,
            validation_action=n.validation_action,
            hand=n.hand,
            measure_number=n.measure_number,
            beat_position=n.beat_position,
        )
        for n in sorted(valid_notes, key=lambda x: x.sequence_index)
    ]

    return TranscriptionNotesResponse(
        transcription_id=t.id,
        model_name=t.model_name,
        model_version=t.model_version,
        note_count=len(notes),
        notes=notes,
    )

from app.services.music_engine.practice_session_service import start_job_session

@router.get(
    "/{job_id}/curriculum",
    summary="Generate curriculum from processed job",
    description="Analyzes the canonical notes of a processed job to generate a full step-by-step learning curriculum."
)
async def get_job_curriculum(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return start_job_session(db, current_user.id, job_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

from pydantic import BaseModel
class ImportSongRequest(BaseModel):
    song_id: str

from app.services.orchestrator.audio_source_manager import SourceManager
from app.services.music_engine.chord_detector import ChordDetector
from app.services.music_engine.key_detector import KeyDetector
from app.services.orchestrator.source_discovery import SourceDiscoveryService
from app.models.song import Song

@router.post(
    "/import-song",
    summary="Import and analyze a song",
    description="Resolves the best source for a song and triggers the full analysis pipeline."
)
async def import_song(
    request: ImportSongRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 0. Load the song
    song = db.query(Song).filter(Song.id == request.song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found.")

    # 1. Resolve existing Source
    source_manager = SourceManager()
    source_info = source_manager.resolve_source(request.song_id, db)
    
    job_id = None
    if source_info["source_type"] == "NONE":
        # 2. Attempt Automatic Source Discovery
        job_id = await SourceDiscoveryService.discover_and_analyze(song, current_user.id, db)
        if not job_id:
            raise HTTPException(
                status_code=400, 
                detail="No valid MIDI or Audio source found for this song. Please upload a source first."
            )
    else:
        # If we found an existing source, we should find its most recent processing job
        existing_job = db.query(ProcessingJob).filter(
            ProcessingJob.audio_asset_id == source_info["asset_id"]
        ).order_by(ProcessingJob.created_at.desc()).first()
        
        if existing_job:
            job_id = str(existing_job.id)
        else:
            # We have a source but no job? Create one.
            import uuid
            job_id = uuid.uuid4()
            processing_job = ProcessingJob(
                id=job_id,
                audio_asset_id=source_info["asset_id"],
                song_id=song.id,
                user_id=current_user.id,
                status=ProcessingJobStage.QUEUED.value,
                progress_percent=0,
                pipeline_version="1.0.0",
                stage_log=[],
            )
            db.add(processing_job)
            db.commit()
            try:
                from app.tasks.transcribe_audio import process_audio_pipeline
                process_audio_pipeline.delay(str(job_id))
            except Exception as e:
                pass
        
    return {
        "status": "success",
        "message": "Song source resolved and queued for analysis.",
        "processing_job_id": str(job_id)
    }
