from app.services.music_engine.note_validator import NoteValidator
from app.models.transcription_note import TranscriptionNote
from app.schemas.pipeline import CanonicalNote

from unittest.mock import MagicMock
from app.core.enums import ValidationAction

def test_note_validator_discards_short_fragments():
    validator = NoteValidator()
    
    # Note under 30ms
    notes = [
        TranscriptionNote(
            id=1, transcription_id="mock", sequence_index=1, midi_number=60, note_name="C4",
            start_time=0.0, end_time=0.02, duration=0.02, velocity=80,
            confidence=0.9, is_validated=False, validation_action=None,
            hand="UNASSIGNED"
        )
    ]
    
    mock_db = MagicMock()
    mock_db.query().filter().order_by().all.return_value = notes
    
    stats = validator.validate_notes("00000000-0000-0000-0000-000000000000", mock_db)
    
    assert stats["discarded"] == 1
    assert notes[0].validation_action == ValidationAction.DISCARD.value
    assert "fragment" in notes[0].validation_reason.lower() or "too short" in notes[0].validation_reason.lower()

def test_note_validator_merges_consecutive_identical():
    validator = NoteValidator()
    
    notes = [
        TranscriptionNote(
            id=1, transcription_id="mock", sequence_index=1, midi_number=60, note_name="C4",
            start_time=0.0, end_time=0.5, duration=0.5, velocity=80,
            confidence=0.9, is_validated=False, validation_action=None,
            hand="UNASSIGNED"
        ),
        # Same pitch, starts 40ms after the first ends (within 80ms threshold)
        TranscriptionNote(
            id=2, transcription_id="mock", sequence_index=2, midi_number=60, note_name="C4",
            start_time=0.54, end_time=1.0, duration=0.46, velocity=80,
            confidence=0.9, is_validated=False, validation_action=None,
            hand="UNASSIGNED"
        )
    ]
    
    mock_db = MagicMock()
    mock_db.query().filter().order_by().all.return_value = notes
    
    stats = validator.validate_notes("00000000-0000-0000-0000-000000000000", mock_db)
    
    assert stats["merged"] == 1
    # The first note should have its end_time extended to 1.0
    assert notes[0].end_time == 1.0
    assert notes[0].duration == 1.0
    # The second note should be discarded
    assert notes[1].validation_action == ValidationAction.DISCARD.value
