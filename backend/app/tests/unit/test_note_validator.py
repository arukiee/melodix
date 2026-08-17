import uuid
from unittest.mock import MagicMock
import pytest
from app.services.music_engine.note_validator import NoteValidator
from app.models.transcription_note import TranscriptionNote
from app.core.enums import ValidationAction

def test_note_validator_micro_note_removal():
    validator = NoteValidator()
    
    # Create notes
    valid_note = TranscriptionNote(
        id=1,
        transcription_id=uuid.uuid4(),
        sequence_index=0,
        midi_number=60,
        note_name="C4",
        start_time=0.0,
        end_time=0.5,
        duration=0.5,
        velocity=80,
        confidence=0.9
    )
    
    micro_note = TranscriptionNote(
        id=2,
        transcription_id=valid_note.transcription_id,
        sequence_index=1,
        midi_number=62,
        note_name="D4",
        start_time=0.6,
        end_time=0.61, # duration 0.01 < 0.03
        duration=0.01,
        velocity=80,
        confidence=0.9
    )
    
    db_mock = MagicMock()
    # Mock chain: db.query().filter().order_by().all() -> [valid_note, micro_note]
    db_mock.query.return_value.filter.return_value.order_by.return_value.all.return_value = [valid_note, micro_note]
    
    stats = validator.validate_notes(str(valid_note.transcription_id), db_mock)
    
    assert stats["total"] == 2
    assert stats["kept"] == 1
    assert stats["discarded"] == 1
    
    assert valid_note.validation_action == ValidationAction.KEEP.value
    assert micro_note.validation_action == ValidationAction.DISCARD.value
    assert "too short" in micro_note.validation_reason.lower()

def test_note_validator_merge_fragments():
    validator = NoteValidator()
    
    note1 = TranscriptionNote(
        id=1, transcription_id=uuid.uuid4(), sequence_index=0, midi_number=60, note_name="C4",
        start_time=0.0, end_time=0.5, duration=0.5, velocity=80, confidence=0.8
    )
    note2 = TranscriptionNote(
        id=2, transcription_id=note1.transcription_id, sequence_index=1, midi_number=60, note_name="C4",
        start_time=0.55, end_time=1.0, duration=0.45, velocity=75, confidence=0.7 # Gap 0.05 < 0.08
    )
    
    db_mock = MagicMock()
    db_mock.query.return_value.filter.return_value.order_by.return_value.all.return_value = [note1, note2]
    
    stats = validator.validate_notes(str(note1.transcription_id), db_mock)
    
    assert stats["total"] == 2
    assert stats["merged"] == 1
    assert stats["discarded"] == 1
    
    assert note1.validation_action == ValidationAction.MERGE.value
    assert note1.end_time == 1.0
    assert note1.duration == 1.0
    
    assert note2.validation_action == ValidationAction.DISCARD.value
