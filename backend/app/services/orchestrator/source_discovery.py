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
from app.schemas.search import SearchResult, SearchFilter
from app.services.search.search_engine import search_engine
import tempfile
import os
import subprocess
from typing import Optional, List
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
    def _extract_youtube_url(song: Song) -> Optional[str]:
        file_url = (song.file_url or '').strip()
        if not file_url:
            return None

        if file_url.startswith(('https://www.youtube.com/watch?', 'https://youtube.com/watch?', 'https://youtu.be/')):
            return file_url

        if re.fullmatch(r'[A-Za-z0-9_-]{11}', file_url):
            return f'https://www.youtube.com/watch?v={file_url}'

        return None

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

        # ── Strategy 2: YouTube audio via yt-dlp (Spotify-guided search & rank) ──────
        # First try a direct URL if the song already has one
        youtube_url = SourceDiscoveryService._extract_youtube_url(song)
        if youtube_url:
            logger.info(f"Trying YouTube audio download for '{song.title}' from {youtube_url}")
            job_id = await SourceDiscoveryService._try_youtube_audio(
                song, user_id, db, youtube_url
            )
            if job_id:
                logger.info(f"YouTube audio queued for '{song.title}' → job {job_id}")
                return job_id

        # Spotify metadata lookup (source of truth for title, artist, album, duration)
        spotify_meta = None
        try:
            from app.services.spotify_client import search_spotify_track
            raw_query = f"{song.title} {song.composer or song.artist or ''}".strip()
            spotify_meta = search_spotify_track(raw_query)
            if spotify_meta:
                logger.info(f"Spotify metadata found for '{song.title}': '{spotify_meta['title']}' by {spotify_meta['artist']} ({spotify_meta['duration_ms']/1000:.1f}s)")
                # Save metadata onto song record
                song.title = spotify_meta["title"]
                if spotify_meta.get("artist"):
                    song.artist = spotify_meta["artist"]
                if spotify_meta.get("album"):
                    song.album = spotify_meta["album"]
                if spotify_meta.get("duration_ms"):
                    song.duration = int(spotify_meta["duration_ms"] / 1000)
                db.commit()
        except Exception as e:
            logger.warning(f"Spotify metadata fetch failed: {e}")

        # Fallback: search YouTube for the best candidate (up to 10 results)
        youtube_provider = search_engine.get_provider("YouTube")
        if youtube_provider:
            if spotify_meta:
                yt_query = f"{spotify_meta['title']} {spotify_meta['artist']}".strip()
            else:
                yt_query = f"{song.title} {song.composer or song.artist or ''}".strip()

            logger.info(f"Searching YouTube for best audio candidate: '{yt_query}'")
            try:
                raw_results = await youtube_provider.search(yt_query, filters=SearchFilter(limit=10))
            except Exception as e:
                logger.warning(f"YouTube search failed: {e}")
                raw_results = []
            if raw_results:
                candidates = list(raw_results)
                best = select_best_candidate(candidates, spotify_metadata=spotify_meta)
                ordered = [best] + [r for r in candidates if r.id != best.id] if best else candidates
                for cand in ordered:
                    is_low_conf = getattr(cand, "low_confidence_match", False)
                    logger.info(f"Selected YouTube candidate: {cand.title} ({cand.id}) from channel {cand.artist} [low_confidence={is_low_conf}]")
                    candidate_url = f"https://www.youtube.com/watch?v={cand.id}"
                    job_id = await SourceDiscoveryService._try_youtube_audio(
                        song, user_id, db, candidate_url
                    )
                    if job_id:
                        logger.info(f"YouTube audio queued for '{song.title}' using candidate {cand.id} → job {job_id}")
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

    # Path to Homebrew-installed ffmpeg; also checked on $PATH as fallback.
    _FFMPEG_LOCATION: str = "/opt/homebrew/bin"

    @staticmethod
    def _download_youtube_audio(youtube_url: str) -> Path:
        """
        Download audio from YouTube using yt-dlp and return the path to the downloaded file.
        Used by the validation script for direct access to the raw wav.

        Uses ``--impersonate chrome-131`` (requires curl_cffi) to bypass
        YouTube's SABR/JS-challenge bot detection, and ``--ffmpeg-location``
        so ffmpeg is found even when it isn't on the shell PATH.
        """
        # Create a temporary directory for the download; it will persist for the duration of the process.
        tmpdir = tempfile.mkdtemp()
        output_template = os.path.join(tmpdir, "%(title)s.%(ext)s")
        cmd = [
            "yt-dlp",
            "--extract-audio",
            "--audio-quality", "0",
            "--no-playlist",
            "--no-warnings",
            "--ignore-errors",
            "--retries", "3",
            "--socket-timeout", "15",
            # Use android,web client to bypass SABR/JS challenge without failing on unsupported impersonation.
            "--extractor-args", "youtube:player_client=android,web",
            # Ensure ffmpeg is found even if not on $PATH.
            "--ffmpeg-location", SourceDiscoveryService._FFMPEG_LOCATION,
            "--output", output_template,
            youtube_url,
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
        except Exception as e:
            logger.error(f"yt-dlp download failed: {e}")
            raise
        # Locate the downloaded file (any extension yt-dlp chose)
        downloaded_files = list(Path(tmpdir).iterdir())
        if not downloaded_files:
            raise RuntimeError("yt-dlp produced no files")
        # Prefer .wav files if present
        wav_files = [p for p in downloaded_files if p.suffix.lower() == ".wav"]
        if wav_files:
            wav_path = wav_files[0]
        else:
            # Convert the first file to WAV using ffmpeg
            src = downloaded_files[0]
            wav_path = src.with_suffix('.wav')
            ffmpeg_bin = os.path.join(SourceDiscoveryService._FFMPEG_LOCATION, "ffmpeg")
            convert_cmd = [ffmpeg_bin, "-y", "-i", str(src), str(wav_path)]
            try:
                subprocess.run(convert_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception as conv_err:
                logger.error(f"ffmpeg conversion failed: {conv_err}")
                raise
            try:
                src.unlink(missing_ok=True)
            except Exception:
                pass
        return wav_path

    @staticmethod
    async def _try_youtube_audio(
        song: Song,
        user_id: uuid.UUID,
        db: Session,
        youtube_url: str,
    ) -> Optional[uuid.UUID]:
        """Download YouTube audio via yt-dlp, then persist and queue the asset.

        Used by discover_and_analyze when a YouTube URL is available.
        """
        # Create temporary directory for yt-dlp output
        with tempfile.TemporaryDirectory() as tmpdir:
            output_template = os.path.join(tmpdir, "%(title)s.%(ext)s")
            cmd = [
                "yt-dlp",
                "--extract-audio",
                "--audio-format", "wav",
                "--audio-quality", "0",
                "--no-playlist",
                "--no-warnings",
                # Bypass SABR/JS challenge via TLS fingerprint impersonation.
                "--impersonate", "chrome-131",
                # Ensure ffmpeg is found even if not on $PATH.
                "--ffmpeg-location", SourceDiscoveryService._FFMPEG_LOCATION,
                "--output", output_template,
                youtube_url,
            ]

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

            wav_files = list(Path(tmpdir).glob("*.wav"))
            if not wav_files:
                all_files = list(Path(tmpdir).iterdir())
                if not all_files:
                    logger.error("yt-dlp produced no output files")
                    return None
                wav_files = all_files

            audio_path = wav_files[0]
            raw_data = audio_path.read_bytes()

        if not raw_data:
            logger.error("Downloaded audio file is empty")
            return None

        logger.info(
            f"Downloaded {len(raw_data) / 1_048_576:.1f} MB from YouTube for '{song.title}'"
        )

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

def select_best_candidate(
    results: List[SearchResult],
    spotify_metadata: Optional[dict] = None,
) -> Optional[SearchResult]:
    """Select the best YouTube candidate using Spotify duration matching (±3s) or keyword fallback."""
    if not results:
        return None

    excluded_keywords = ['live', 'reaction', 'tutorial', 'mashup', 'concert', 'full album', '1 hour', 'extended mix']
    preferred_keywords = ['official audio', 'official video']

    def _score(r: SearchResult) -> float:
        s = 0.0
        title_lower = (getattr(r, 'title', '') or '').lower()
        if any(kw in title_lower for kw in preferred_keywords):
            s += 100
        s += getattr(r, 'popularity', 0) / 1_000_000
        return s

    # 1. Spotify Duration Match (tolerance ±3.0 seconds)
    if spotify_metadata and spotify_metadata.get("duration_ms"):
        spotify_sec = spotify_metadata["duration_ms"] / 1000.0
        duration_matched = [
            r for r in results
            if abs(getattr(r, 'duration', 0) - spotify_sec) <= 3.0
            and not any(kw in (getattr(r, 'title', '') or '').lower() for kw in excluded_keywords)
        ]
        if duration_matched:
            topic_matches = [
                r for r in duration_matched
                if (getattr(r, 'artist', '') or '').endswith(' Topic')
            ]
            best = topic_matches[0] if topic_matches else max(duration_matched, key=_score)
            best.low_confidence_match = False
            return best

    # 2. Fallback: Keyword & Popularity Scoring (low_confidence_match = True if Spotify duration matched 0 candidates)
    candidates = [
        r for r in results
        if 60 <= getattr(r, 'duration', 0) <= 480
        and not any(kw in (getattr(r, 'title', '') or '').lower() for kw in excluded_keywords)
    ]
    if not candidates:
        candidates = results

    topic_matches = [
        r for r in candidates
        if (getattr(r, 'artist', '') or '').endswith(' Topic')
    ]
    best = topic_matches[0] if topic_matches else max(candidates, key=_score)
    best.low_confidence_match = spotify_metadata is not None
    return best

