import pytest
from app.services.music_engine.difficulty_engine import DifficultyEngine, DifficultyMetrics
from app.models.transcription_note import TranscriptionNote

def test_difficulty_metrics_computation():
    engine = DifficultyEngine()
    
    # Create some mock notes
    notes = [
        TranscriptionNote(id=1, midi_number=60, start_time=0.0, end_time=0.5, duration=0.5, hand="RIGHT"),
        TranscriptionNote(id=2, midi_number=64, start_time=0.5, end_time=1.0, duration=0.5, hand="RIGHT"),
        TranscriptionNote(id=3, midi_number=67, start_time=1.0, end_time=1.5, duration=0.5, hand="RIGHT"),
        # Chord (polyphony)
        TranscriptionNote(id=4, midi_number=60, start_time=1.5, end_time=2.0, duration=0.5, hand="LEFT"),
        TranscriptionNote(id=5, midi_number=64, start_time=1.5, end_time=2.0, duration=0.5, hand="RIGHT"),
    ]
    
    metrics = engine._compute_metrics(notes, tempo_bpm=120.0)
    
    assert metrics.notes_per_second == 5 / 2.0  # 5 notes in 2 seconds = 2.5
    assert metrics.pitch_range_semitones == 7   # 67 - 60
    assert metrics.max_simultaneous_notes == 2  # The chord at 1.5s
    assert metrics.polyphony_ratio > 0.0

def test_importance_scoring():
    engine = DifficultyEngine()
    
    # Create notes where one is clearly more "important" (louder, longer, higher pitch)
    melody_note = TranscriptionNote(
        id=1, midi_number=72, start_time=0.0, end_time=1.0, duration=1.0, velocity=100
    )
    accompaniment_note = TranscriptionNote(
        id=2, midi_number=48, start_time=0.0, end_time=0.2, duration=0.2, velocity=40
    )
    
    notes = [melody_note, accompaniment_note]
    engine._compute_importance_scores(notes)
    
    # Melody note should score higher due to pitch salience, velocity, and duration
    assert getattr(melody_note, 'importance_score', 0) > getattr(accompaniment_note, 'importance_score', 0)
