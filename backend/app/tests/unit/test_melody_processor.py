import numpy as np

from app.services.music_engine.melody_processor import clean_melody_events, melody_payload


def test_cleanup_keeps_highest_confidence_note_and_quantizes(monkeypatch, tmp_path):
    audio_path = tmp_path / "stem.wav"
    audio_path.write_bytes(b"placeholder")
    monkeypatch.setattr("librosa.load", lambda *args, **kwargs: (np.zeros(22050), 22050))
    monkeypatch.setattr("librosa.feature.tempo", lambda *args, **kwargs: np.array([120.0]))
    monkeypatch.setattr(
        "app.services.music_engine.melody_processor._pyin_pitch",
        lambda *args, **kwargs: None,
    )

    events = clean_melody_events([
        (0.01, 0.49, 60, 80, 0.7),
        (0.01, 0.49, 64, 100, 0.9),
        (0.51, 0.99, 62, 90, 0.8),
    ], str(audio_path))

    assert [(event[0], event[1], event[2]) for event in events] == [
        (0.0, 0.5, 64),
        (0.5, 1.0, 62),
    ]
    assert melody_payload(events) == [
        {"note": "E4", "midiNumber": 64, "startTime": 0.0, "duration": 0.5},
        {"note": "D4", "midiNumber": 62, "startTime": 0.5, "duration": 0.5},
    ]


def test_cleanup_prefers_coherent_melody_over_isolated_high_accompaniment(monkeypatch, tmp_path):
    audio_path = tmp_path / "stem.wav"
    audio_path.write_bytes(b"placeholder")
    monkeypatch.setattr("librosa.load", lambda *args, **kwargs: (np.zeros(22050), 22050))
    monkeypatch.setattr("librosa.feature.tempo", lambda *args, **kwargs: np.array([120.0]))
    monkeypatch.setattr(
        "app.services.music_engine.melody_processor._pyin_pitch",
        lambda *args, **kwargs: None,
    )

    events = clean_melody_events([
        (0.0, 0.5, 64, 90, 0.85),
        (0.0, 0.5, 84, 90, 0.95),  # brief high harmonic/accompaniment candidate
        (0.5, 1.0, 65, 90, 0.85),
        (1.0, 1.5, 67, 90, 0.85),
    ], str(audio_path))

    assert [event[2] for event in events] == [64, 65, 67]
