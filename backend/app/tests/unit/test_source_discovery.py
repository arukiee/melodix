"""
Unit tests for SourceDiscoveryService.

Tests:
  - BitMidi discovery success (downloads MIDI file, persists asset, queues job).
  - BitMidi returns no results, falls back to YouTube URL download via yt-dlp,
    mocking the subprocess execution and file system output.
"""

from __future__ import annotations

import os
import uuid
import pytest
import tempfile
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

from app.models.song import Song
from app.models.audio_asset import AudioAsset
from app.models.processing_job import ProcessingJob
from app.services.orchestrator.source_discovery import SourceDiscoveryService


class DummySearchResult:
    def __init__(self, item_id: str, title: str):
        self.id = item_id
        self.title = title
        self.provider = "BitMidi"


@pytest.mark.anyio
async def test_discover_and_analyze_bitmidi_success():
    """Verify that if BitMidi returns a result, we download it and skip YouTube."""
    db_mock = MagicMock()
    # No existing assets
    db_mock.query.return_value.filter.return_value.first.return_value = None

    user_id = uuid.uuid4()
    song = Song(
        id=uuid.uuid4(),
        title="Ode to Joy",
        composer="Beethoven",
        file_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ", # Has YouTube URL, but BitMidi should win first
    )

    # Mock BitMidi provider
    mock_provider = AsyncMock()
    mock_provider.search.return_value = [DummySearchResult("bitmidi-123", "Ode to Joy")]
    mock_provider.get_raw_data.return_value = b"mock-midi-data-bytes"

    # Mock search_engine.get_provider
    with patch("app.services.orchestrator.source_discovery.search_engine.get_provider", return_value=mock_provider), \
         patch("app.storage.minio_service.minio_service", create=True) as mock_minio, \
         patch("app.tasks.transcribe_audio.process_audio_pipeline.delay") as mock_celery_delay:

        job_id = await SourceDiscoveryService.discover_and_analyze(song, user_id, db_mock)

        assert job_id is not None
        assert mock_provider.search.called
        assert mock_provider.get_raw_data.called
        mock_minio.upload_bytes.assert_called_once()
        mock_celery_delay.assert_called_once_with(str(job_id))

        assert db_mock.add.call_count == 2 # 1 AudioAsset + 1 ProcessingJob
        db_mock.commit.assert_called_once()


@pytest.mark.anyio
async def test_discover_and_analyze_youtube_fallback_success():
    """Verify that if BitMidi returns nothing, we fall back to downloading YouTube audio via yt-dlp."""
    db_mock = MagicMock()
    db_mock.query.return_value.filter.return_value.first.return_value = None

    user_id = uuid.uuid4()
    song = Song(
        id=uuid.uuid4(),
        title="Perfect",
        composer="Ed Sheeran",
        file_url="https://www.youtube.com/watch?v=2Vv-BfVoq4g", # YouTube URL present
    )

    # BitMidi returns no results
    mock_provider = AsyncMock()
    mock_provider.search.return_value = []

    # Mock subprocess call to simulate successful yt-dlp download
    mock_proc = AsyncMock()
    mock_proc.returncode = 0
    mock_proc.communicate.return_value = (b"ytdlp stdout", b"ytdlp stderr")

    # We also mock write_bytes / read_bytes on the downloaded file by patching tempfile.TemporaryDirectory
    # and writing a dummy wav file inside it.
    original_tempdir = tempfile.TemporaryDirectory

    class MockTemporaryDirectory:
        def __init__(self, *args, **kwargs):
            self.temp_dir = original_tempdir(*args, **kwargs)
            self.name = self.temp_dir.name
            # Create a dummy wav file so glob works
            dummy_file = Path(self.name) / "audio.wav"
            dummy_file.write_bytes(b"mock-downloaded-wav-data")

        def __enter__(self):
            return self.name

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.temp_dir.__exit__(exc_type, exc_val, exc_tb)

    with patch("app.services.orchestrator.source_discovery.search_engine.get_provider", return_value=mock_provider), \
         patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec, \
         patch("tempfile.TemporaryDirectory", MockTemporaryDirectory), \
         patch("app.storage.minio_service.minio_service", create=True) as mock_minio, \
         patch("app.tasks.transcribe_audio.process_audio_pipeline.delay") as mock_celery_delay:

        job_id = await SourceDiscoveryService.discover_and_analyze(song, user_id, db_mock)

        assert job_id is not None
        assert mock_provider.search.called
        assert mock_exec.called
        # Production installs yt-dlp as a console script (the same command used
        # by Docker and the local virtualenv), so invoke that supported entry
        # point instead of assuming a particular system Python executable.
        args, kwargs = mock_exec.call_args
        assert args[0] == "yt-dlp"
        assert "https://www.youtube.com/watch?v=2Vv-BfVoq4g" in args

        mock_minio.upload_bytes.assert_called_once()
        # Verify it uploaded WAV
        upload_args = mock_minio.upload_bytes.call_args[1]
        assert upload_args.get("content_type") == "audio/wav"

        mock_celery_delay.assert_called_once_with(str(job_id))

        assert db_mock.add.call_count == 2
        db_mock.commit.assert_called_once()
