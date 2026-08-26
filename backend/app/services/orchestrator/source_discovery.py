"""
Source discovery service.

Attempts to find a valid audio source for a song in order:

  1. BitMidi MIDI search  — good for classical / public domain songs
  2. YouTube audio download via yt-dlp — fallback for modern pop/rock songs
     that have a known YouTube URL stored on song.file_url

Returns a ProcessingJob UUID if a source is found and the pipeline is queued,
or None if no source could be located.
"""

import uuid
import hashlib
import logging
import asyncio
import re
import tempfile
import os
from typing import Optional
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.song import Song
from app.models.audio_asset import AudioAsset
from app.models.processing_job import ProcessingJob
from app.core.enums import AudioSourceType, ProcessingJobStage
from app.services.search.search_engine import search_engine

logger = logging.getLogger(__name__)


class SourceDiscoveryService:

    @staticmethod
    async def discover_and_analyze(
        song: Song,
        user_id: uuid.UUID,
        db: Session,
    ) -> Optional[uuid.UUID]:
        """
        Try to automatically discover a valid MIDI/Audio source for the song.

        Strategy:
          1. BitMidi MIDI search (public domain / classical)
          2. YouTube audio download via yt-dlp (modern songs with YouTube URL)

        Returns the ProcessingJob ID if successful, else None.
        """
        # ── Strategy 1: BitMidi ────────────────────────────────────────────
        job_id = await SourceDiscoveryService._try_bitmidi(song, user_id, db)
        if job_id:
            logger.info(f"BitMidi source found for '{song.title}' → job {job_id}")
            return job_id

        # ── Strategy 2: YouTube audio via yt-dlp ──────────────────────────
        youtube_url = SourceDiscoveryService._extract_youtube_url(song)
        if youtube_url:
            logger.info(f"Trying YouTube audio download for '{song.title}' from {youtube_url}")
            job_id = await SourceDiscoveryService._try_youtube_audio(
                song, user_id, db, youtube_url
            )
            if job_id:
                logger.info(f"YouTube audio queued for '{song.title}' → job {job_id}")
                return job_id

        logger.info(f"No automatic source found for '{song.title}'")
        return None

    # ──────────────────────────────────────────────────────────────────────
    # Strategy 1: BitMidi
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    async def _try_bitmidi(
        song: Song,
        user_id: uuid.UUID,
        db: Session,
    ) -> Optional[uuid.UUID]:
        """Search BitMidi for a MIDI file matching the song title."""
        clean_title = re.sub(r'(?i)(\(.*?\)|\{.*?\}|\[.*?\]|ft\..*|feat\..*|-)', '', song.title).strip()
        query = f"{clean_title} {song.composer or ''}".strip()
        logger.info(f"BitMidi search: '{query}'")

        bitmidi = search_engine.get_provider("BitMidi")
        if not bitmidi:
            logger.warning("BitMidi provider not registered — skipping.")
            return None

        from app.schemas.search import SearchFilter
        filters = SearchFilter(limit=1)
        try:
            results = await bitmidi.search(query, filters=filters, db=db)
        except Exception as e:
            logger.warning(f"BitMidi search error: {e}")
            return None

        if not results:
            return None

        best_match = results[0]
        logger.info(f"BitMidi match: {best_match.title} ({best_match.id})")

        try:
            raw_data = await bitmidi.get_raw_data(best_match.id)
            if not raw_data:
                return None
        except Exception as e:
            logger.error(f"BitMidi raw data fetch failed: {e}")
            return None

        return SourceDiscoveryService._persist_asset_and_queue(
            raw_data=raw_data,
            audio_format="mid",
            content_type="audio/midi",
            original_filename=f"{best_match.title}.mid",
            song=song,
            user_id=user_id,
            db=db,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Strategy 2: YouTube audio via yt-dlp
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_youtube_url(song: Song) -> Optional[str]:
        """Extract YouTube URL from song.file_url if it points to YouTube."""
        if not song.file_url:
            return None
        url = song.file_url.strip()
        # Accept youtube.com/watch?v=... or youtu.be/... links
        if "youtube.com/watch" in url or "youtu.be/" in url:
            return url
        return None

    @staticmethod
    async def _try_youtube_audio(
        song: Song,
        user_id: uuid.UUID,
        db: Session,
        youtube_url: str,
    ) -> Optional[uuid.UUID]:
        """
        Download audio from YouTube using yt-dlp, save to MinIO, and queue the
        full audio analysis pipeline.

        yt-dlp is called with:
          --format bestaudio[ext=m4a]/bestaudio/best
          --extract-audio --audio-format wav
          --audio-quality 0
        so Basic Pitch receives a WAV file.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_template = os.path.join(tmpdir, "audio.%(ext)s")
            cmd = [
                "python3", "-m", "yt_dlp",
                youtube_url,
                "--format", "bestaudio[ext=m4a]/bestaudio/best",
                "--extract-audio",
                "--audio-format", "wav",
                "--audio-quality", "0",
                "--no-playlist",
                "--no-warnings",
                "--output", output_template,
            ]
            logger.info(f"yt-dlp command: {' '.join(cmd)}")

            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
            except asyncio.TimeoutError:
                logger.error("yt-dlp timed out (> 5 min) — aborting YouTube download")
                return None
            except FileNotFoundError:
                logger.error("yt-dlp not found in PATH — install it with: pip install yt-dlp")
                return None
            except Exception as e:
                logger.error(f"yt-dlp subprocess error: {e}")
                return None

            if proc.returncode != 0:
                logger.error(
                    f"yt-dlp failed (exit {proc.returncode}): "
                    f"{stderr.decode('utf-8', errors='replace')[:500]}"
                )
                return None

            # Find the downloaded WAV file
            wav_files = list(Path(tmpdir).glob("*.wav"))
            if not wav_files:
                # yt-dlp may have saved as a different extension
                all_files = list(Path(tmpdir).iterdir())
                if not all_files:
                    logger.error("yt-dlp produced no output files")
                    return None
                wav_files = all_files  # Use whatever was downloaded

            audio_path = wav_files[0]
            raw_data = audio_path.read_bytes()

        if not raw_data:
            logger.error("Downloaded audio file is empty")
            return None

        logger.info(
            f"Downloaded {len(raw_data) / 1_048_576:.1f} MB from YouTube for '{song.title}'"
        )

        # Determine file extension
        audio_format = "wav"
        content_type = "audio/wav"

        return SourceDiscoveryService._persist_asset_and_queue(
            raw_data=raw_data,
            audio_format=audio_format,
            content_type=content_type,
            original_filename=f"{song.title}.{audio_format}",
            song=song,
            user_id=user_id,
            db=db,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Shared: persist asset + queue Celery task
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _persist_asset_and_queue(
        *,
        raw_data: bytes,
        audio_format: str,
        content_type: str,
        original_filename: str,
        song: Song,
        user_id: uuid.UUID,
        db: Session,
    ) -> Optional[uuid.UUID]:
        """
        Save audio bytes to MinIO, create AudioAsset + ProcessingJob records,
        and dispatch the Celery transcription task.
        """
        file_hash = hashlib.sha256(raw_data).hexdigest()

        # De-duplication check
        existing_asset = db.query(AudioAsset).filter(
            AudioAsset.file_hash_sha256 == file_hash,
            AudioAsset.user_id == user_id,
        ).first()

        if existing_asset:
            existing_job = (
                db.query(ProcessingJob)
                .filter(ProcessingJob.audio_asset_id == existing_asset.id)
                .order_by(ProcessingJob.created_at.desc())
                .first()
            )
            if existing_job:
                # Re-dispatch if stuck
                if existing_job.status in {
                    ProcessingJobStage.QUEUED.value, ProcessingJobStage.FAILED.value,
                    "queued", "failed", "QUEUED", "FAILED",
                }:
                    try:
                        from app.tasks.transcribe_audio import process_audio_pipeline
                        process_audio_pipeline.delay(str(existing_job.id))
                    except Exception as e:
                        logger.warning(f"Re-dispatch failed: {e}")
                return existing_job.id

        asset_id = uuid.uuid4()
        storage_path = f"audio/{asset_id}/original.{audio_format}"

        try:
            from app.storage.minio_service import minio_service
            minio_service.upload_bytes(storage_path, raw_data, content_type=content_type)
        except Exception as e:
            logger.error(f"MinIO upload failed: {e}")
            return None

        audio_asset = AudioAsset(
            id=asset_id,
            user_id=user_id,
            song_id=song.id,
            source_type=AudioSourceType.PUBLIC_DOMAIN.value,
            original_filename=original_filename,
            file_hash_sha256=file_hash,
            storage_path=storage_path,
            format=audio_format,
            file_size_bytes=len(raw_data),
            is_valid=False,
        )
        db.add(audio_asset)

        job_id = uuid.uuid4()
        processing_job = ProcessingJob(
            id=job_id,
            audio_asset_id=asset_id,
            song_id=song.id,
            user_id=user_id,
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
            logger.warning(f"Celery dispatch failed (job saved, will retry): {e}")

        return job_id
