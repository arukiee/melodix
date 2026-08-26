import pytest
from unittest.mock import MagicMock
from app.services.music_engine.note_validator import NoteValidator
from app.services.music_engine.importers.chord_extractor import ChordExtractor, parse_pitch_class
from app.services.music_engine.chord_detector import ChordDetector
from app.services.music_engine.transcription_service import TranscriptionService
from app.core.enums import ValidationAction

class DummyNote:
    def __init__(self, note_id, midi_number, note_name, start_time, end_time, velocity=80, confidence=0.9):
        self.id = note_id
        self.transcription_id = 'test-id'
        self.midi_number = midi_number
        self.note_name = note_name
        self.start_time = start_time
        self.end_time = end_time
        self.duration = end_time - start_time
        self.velocity = velocity
        self.confidence = confidence
        self.validation_action = None
        self.validation_reason = None
        self.is_validated = False


def test_polyphonic_overlap_preservation():
    """Verify that polyphonic overlapping notes of the same pitch are kept, not discarded."""
    db = MagicMock()
    n1 = DummyNote(1, 60, 'C4', 0.0, 2.0)
    n2 = DummyNote(2, 60, 'C4', 0.5, 1.2) # re-strike during sustain
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [n1, n2]

    validator = NoteValidator()
    stats = validator.validate_notes('00000000-0000-0000-0000-000000000000', db)

    # Both notes must be kept
    assert stats['kept'] == 2
    assert stats['discarded'] == 0
    assert n1.validation_action == ValidationAction.KEEP.value
    assert n2.validation_action == ValidationAction.KEEP.value


def test_accidental_preservation_and_pitch_parsing():
    """Verify accidental preservation for C#, Eb, F#, Ab, etc."""
    p_name, pc, oct_num = parse_pitch_class("C#4")
    assert p_name == "C#"
    assert pc == 1

    p_name, pc, oct_num = parse_pitch_class("Eb3")
    assert p_name == "Eb"
    assert pc == 3

    p_name, pc, oct_num = parse_pitch_class("F#5")
    assert p_name == "F#"
    assert pc == 6


def test_chord_extractor_accidental_triads_and_inversions():
    """Verify ChordExtractor accurately detects C# Minor, D Major, Eb Major7, and inversions."""
    notes_csharp_min = [
        {"note": "C#4", "measure": 0},
        {"note": "E4", "measure": 0},
        {"note": "G#4", "measure": 0},
    ]
    chords_csm = ChordExtractor.extract_chords(notes_csharp_min)
    assert len(chords_csm) == 1
    assert "C#m" in chords_csm[0]["detected_chord"]

    notes_d_maj = [
        {"note": "D4", "measure": 1},
        {"note": "F#4", "measure": 1},
        {"note": "A4", "measure": 1},
    ]
    chords_d = ChordExtractor.extract_chords(notes_d_maj)
    assert len(chords_d) == 1
    assert "D Major Triad" in chords_d[0]["detected_chord"]

    # Inversion: E in bass for C Major (E3 - G3 - C4)
    notes_c_inv = [
        {"note": "E3", "measure": 2},
        {"note": "G3", "measure": 2},
        {"note": "C4", "measure": 2},
    ]
    chords_inv = ChordExtractor.extract_chords(notes_c_inv)
    assert len(chords_inv) == 1
    assert "/E" in chords_inv[0]["detected_chord"]


def test_chord_detector_match_chord():
    """Verify ChordDetector match_chord supports 7th chords and inversions."""
    detector = ChordDetector()

    # C Major / E bass (pitch classes 0, 4, 7 with bass=4)
    name, score = detector.match_chord(root=0, pitch_classes=[0, 4, 7], bass_note=4)
    assert score >= 0.70
    assert "C/E" in name

    # G Dominant 7th (pitch classes 7, 11, 2, 5 with bass=7)
    name, score = detector.match_chord(root=7, pitch_classes=[7, 11, 2, 5], bass_note=7)
    assert score >= 0.70
    assert "G7" in name
