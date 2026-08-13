import pytest
from app.services.music_engine.importers.validator import ImportValidator
from app.services.music_engine.importers.chord_extractor import ChordExtractor

def test_validator_detects_errors():
    invalid_song = {
        "title": "",
        "bpm": 20, # too low
        "time_signature": "4-4", # invalid format
        "notes": [
            {"note": "C4", "duration": -1.0, "measure": 0} # invalid duration
        ]
    }
    errors = ImportValidator.validate(invalid_song)
    assert len(errors) >= 4
    assert any("title" in err for err in errors)
    assert any("BPM" in err for err in errors)
    assert any("time signature" in err for err in errors)
    assert any("duration" in err for err in errors)
    assert any("key signature" in err.lower() for err in errors)

def test_validator_passes_valid_song():
    valid_song = {
        "title": "Au Clair de la Lune",
        "bpm": 80,
        "time_signature": "4/4",
        "key_signature": "C Major",
        "notes": [
            {"note": "C4", "duration": 1.0, "measure": 0}
        ]
    }
    errors = ImportValidator.validate(valid_song)
    assert len(errors) == 0

def test_validator_unusual_time_signature():
    song = {
        "title": "Odd Meter Song",
        "bpm": 120,
        "time_signature": "7/8",
        "key_signature": "G Major",
        "notes": [{"note": "C4", "duration": 1.0, "measure": 0}]
    }
    errors = ImportValidator.validate(song)
    assert any("unusual" in err.lower() for err in errors)

def test_chord_extractor_major_triad():
    notes = [
        {"note": "C4", "duration": 1.0, "measure": 0},
        {"note": "E4", "duration": 1.0, "measure": 0},
        {"note": "G4", "duration": 1.0, "measure": 0}
    ]
    chords = ChordExtractor.extract_chords(notes)
    assert len(chords) == 1
    assert chords[0]["detected_chord"] == "C Major Triad"

def test_chord_extractor_dyad():
    notes = [
        {"note": "D4", "duration": 1.0, "measure": 1},
        {"note": "F4", "duration": 1.0, "measure": 1}
    ]
    chords = ChordExtractor.extract_chords(notes)
    assert len(chords) == 1
    assert "D" in chords[0]["pitches"]
    assert "F" in chords[0]["pitches"]
    assert "Dyad" in chords[0]["detected_chord"]
