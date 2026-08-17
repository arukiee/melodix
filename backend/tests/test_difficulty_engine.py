import pytest
from app.services.music_engine.difficulty_engine import DifficultyEngine, DifficultyLevel
from app.models.transcription_note import TranscriptionNote
import copy

def test_difficulty_engine_metrics():
    engine = DifficultyEngine()
    
    # 4 notes total, 2 playing simultaneously
    notes = [
        TranscriptionNote(id=1, transcription_id="mock", sequence_index=1, midi_number=60, note_name="C4", start_time=0.0, end_time=1.0, duration=1.0, velocity=80, hand="UNASSIGNED"),
        TranscriptionNote(id=2, transcription_id="mock", sequence_index=2, midi_number=64, note_name="E4", start_time=0.0, end_time=1.0, duration=1.0, velocity=80, hand="UNASSIGNED"),
        TranscriptionNote(id=3, transcription_id="mock", sequence_index=3, midi_number=67, note_name="G4", start_time=2.0, end_time=3.0, duration=1.0, velocity=80, hand="UNASSIGNED"),
        TranscriptionNote(id=4, transcription_id="mock", sequence_index=4, midi_number=72, note_name="C5", start_time=3.0, end_time=4.0, duration=1.0, velocity=80, hand="UNASSIGNED"),
    ]
    
    metrics = engine._compute_metrics(notes, 120.0)
    
    assert metrics.notes_per_second > 0
    # Max simultaneous notes should be 2 (C4 and E4 at t=0.0)
    assert metrics.max_simultaneous_notes == 2
    
def test_difficulty_engine_easy_variant():
    engine = DifficultyEngine()
    
    notes = [
        # Melody
        TranscriptionNote(id=1, transcription_id="mock", sequence_index=1, midi_number=72, note_name="C5", start_time=0.0, end_time=1.0, duration=1.0, velocity=80, hand="RIGHT"),
        # Harmony chord (simultaneous)
        TranscriptionNote(id=2, transcription_id="mock", sequence_index=2, midi_number=60, note_name="C4", start_time=0.0, end_time=1.0, duration=1.0, velocity=80, hand="LEFT"),
        TranscriptionNote(id=3, transcription_id="mock", sequence_index=3, midi_number=64, note_name="E4", start_time=0.0, end_time=1.0, duration=1.0, velocity=80, hand="LEFT"),
        TranscriptionNote(id=4, transcription_id="mock", sequence_index=4, midi_number=67, note_name="G4", start_time=0.0, end_time=1.0, duration=1.0, velocity=80, hand="LEFT"),
    ]
    
    # We assign importance score to simulate _compute_importance_scores
    notes[0].importance_score = 0.9
    notes[1].importance_score = 0.4
    notes[2].importance_score = 0.5
    notes[3].importance_score = 0.6
    
    variant_notes = engine._simplify_to_single_notes(notes)
    
    # Easy mode typically drops non-essential polyphony or complex left-hand chords.
    # The exact heuristic depends on `difficulty_engine.py`, but it should have fewer than 4 notes.
    assert len(variant_notes) < 4
