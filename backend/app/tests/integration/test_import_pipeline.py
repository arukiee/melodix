"""
End-to-end integration tests for the full import pipeline.
Uses FastAPI TestClient with the real app (but mock DB for commit tests).
"""
import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.factory import create_app
from app.core.database import get_db

app = create_app()

# ─── Helpers ───────────────────────────────────────────────

VALID_MUSICXML = b"""<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <work><work-title>Integration Test Song</work-title></work>
  <identification>
    <creator type="composer">Test Composer</creator>
  </identification>
  <part-list><score-part id="P1"><part-name>Piano</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key><fifths>0</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time>
      </attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration></note>
      <note><pitch><step>E</step><octave>4</octave></pitch><duration>4</duration></note>
      <note><pitch><step>G</step><octave>4</octave></pitch><duration>4</duration></note>
    </measure>
    <measure number="2">
      <note><pitch><step>D</step><octave>4</octave></pitch><duration>4</duration></note>
      <note><pitch><step>F</step><octave>4</octave></pitch><duration>4</duration></note>
      <note><pitch><step>A</step><octave>4</octave></pitch><duration>4</duration></note>
    </measure>
  </part>
</score-partwise>"""

VALID_MIDI_HEADER = b"MThd" + b"\x00" * 100  # Triggers the MIDI path (mock parse)

CORRUPT_XML = b"<this is not valid xml at all <<<>>>"

EMPTY_FILE = b""


client = TestClient(app)


# ─── Preview Tests ─────────────────────────────────────────

class TestPreviewEndpoint:
    def test_valid_musicxml_preview(self):
        """Full pipeline: upload valid MusicXML → get preview with metadata, chords, missions."""
        resp = client.post(
            "/api/v1/import/preview",
            files={"file": ("test_song.xml", io.BytesIO(VALID_MUSICXML), "application/xml")}
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["title"] == "Integration Test Song"
        assert data["composer"] == "Test Composer"
        assert data["key_signature"] == "C Major"
        assert data["time_signature"] == "4/4"
        assert data["note_count"] == 6
        assert data["measure_count"] == 2
        assert len(data["generated_missions"]) >= 2
        assert len(data["detected_chords"]) >= 1

    def test_valid_midi_preview(self):
        """MIDI upload falls through to mock parser, returning a valid preview."""
        resp = client.post(
            "/api/v1/import/preview",
            files={"file": ("song.mid", io.BytesIO(VALID_MIDI_HEADER), "audio/midi")}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "MIDI Imported Song"
        assert data["note_count"] >= 1

    def test_corrupt_xml_preview(self):
        """Corrupt XML falls back to mock importer — no crash."""
        resp = client.post(
            "/api/v1/import/preview",
            files={"file": ("bad.xml", io.BytesIO(CORRUPT_XML), "application/xml")}
        )
        # MusicXMLImporter falls back to mock, so still 200
        assert resp.status_code == 200

    def test_empty_file_rejected(self):
        """Empty file should be rejected with 400."""
        resp = client.post(
            "/api/v1/import/preview",
            files={"file": ("empty.xml", io.BytesIO(EMPTY_FILE), "application/xml")}
        )
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    def test_unsupported_extension_rejected(self):
        """Non-music file extensions should be rejected with 415."""
        resp = client.post(
            "/api/v1/import/preview",
            files={"file": ("photo.jpg", io.BytesIO(b"fake"), "image/jpeg")}
        )
        assert resp.status_code == 415
        assert "Unsupported" in resp.json()["detail"]

    def test_oversized_file_rejected(self):
        """Files over 5 MB should be rejected with 413."""
        big_file = b"x" * (6 * 1024 * 1024)
        resp = client.post(
            "/api/v1/import/preview",
            files={"file": ("big.xml", io.BytesIO(big_file), "application/xml")}
        )
        assert resp.status_code == 413
        assert "too large" in resp.json()["detail"].lower()

    def test_preview_includes_validation_warnings(self):
        """Songs with issues should surface validation warnings in the preview."""
        resp = client.post(
            "/api/v1/import/preview",
            files={"file": ("test.xml", io.BytesIO(VALID_MUSICXML), "application/xml")}
        )
        data = resp.json()
        # validation_warnings should be a list (may be empty for valid files)
        assert isinstance(data["validation_warnings"], list)

    def test_preview_missions_have_structure(self):
        """Each generated mission should have required fields."""
        resp = client.post(
            "/api/v1/import/preview",
            files={"file": ("test.xml", io.BytesIO(VALID_MUSICXML), "application/xml")}
        )
        data = resp.json()
        for mission in data["generated_missions"]:
            assert "id" in mission
            assert "title" in mission
            assert "type" in mission
            assert "bpm" in mission
            assert "xpReward" in mission


# ─── Commit Tests (with mocked DB) ────────────────────────

class TestCommitEndpoint:
    def _mock_db(self):
        """Create a mock DB session for commit tests."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        # Make the Song mock return an id after refresh
        def mock_refresh(obj):
            import uuid
            obj.id = uuid.uuid4()
        mock_session.refresh = mock_refresh

        return mock_session

    def test_commit_valid_musicxml(self):
        """Valid MusicXML → commit succeeds → song persisted."""
        mock_session = self._mock_db()
        app.dependency_overrides[get_db] = lambda: mock_session

        try:
            resp = client.post(
                "/api/v1/import/commit",
                files={"file": ("song.xml", io.BytesIO(VALID_MUSICXML), "application/xml")}
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert "Integration Test Song" in data["message"]
            assert data["song_id"] is not None

            # Verify DB was called
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called()
        finally:
            app.dependency_overrides.clear()

    def test_commit_empty_file_rejected(self):
        """Empty file should not reach commit logic."""
        resp = client.post(
            "/api/v1/import/commit",
            files={"file": ("empty.xml", io.BytesIO(EMPTY_FILE), "application/xml")}
        )
        assert resp.status_code == 400

    def test_commit_unsupported_type_rejected(self):
        """Non-music files should not reach commit logic."""
        resp = client.post(
            "/api/v1/import/commit",
            files={"file": ("doc.pdf", io.BytesIO(b"fake"), "application/pdf")}
        )
        assert resp.status_code == 415
