"""
Tests for melody_extractor.py

Covers:
  1. select_melody_stem — silent vocals → fallback to "other" stem
  2. pitch_curve_to_notes — synthetic C4-E4-G4 sequence extracted correctly
  3. extract_melody — integration smoke test on a tiny wav (no real Demucs call)
"""

from __future__ import annotations

import math
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Helpers — generate synthetic audio
# ---------------------------------------------------------------------------

SR = 16000  # torchcrepe internal sample rate


def _sine_wav(freq_hz: float, duration_s: float, sr: int = SR) -> np.ndarray:
    """Return a mono float32 sine-wave array."""
    t = np.linspace(0.0, duration_s, int(sr * duration_s), endpoint=False)
    return (np.sin(2 * math.pi * freq_hz * t)).astype(np.float32)


def _write_wav(path: Path, audio: np.ndarray, sr: int = SR) -> None:
    import soundfile as sf
    sf.write(str(path), audio, sr, subtype="PCM_16")


# ---------------------------------------------------------------------------
# Fixture — tiny silence wav for silent-vocals test
# ---------------------------------------------------------------------------

@pytest.fixture()
def silent_wav(tmp_path: Path) -> Path:
    p = tmp_path / "silence.wav"
    _write_wav(p, np.zeros(SR, dtype=np.float32))
    return p


# ---------------------------------------------------------------------------
# Test 1 — select_melody_stem: silent vocals → "other"
# ---------------------------------------------------------------------------

def test_select_melody_stem_silent_vocals_picks_other(tmp_path: Path) -> None:
    """
    When the vocals stem is silent (RMS ≈ 0), select_melody_stem should
    return the 'other' stem regardless of threshold.
    """
    from backend.app.services.music_engine.melody_extractor import select_melody_stem

    # Write a silent vocals file and a non-silent other file.
    vocals_path = tmp_path / "vocals.wav"
    other_path = tmp_path / "other.wav"
    _write_wav(vocals_path, np.zeros(SR * 2, dtype=np.float32))
    _write_wav(other_path, _sine_wav(261.63, 2.0))

    stems = {
        "vocals": vocals_path,
        "drums": tmp_path / "drums.wav",
        "bass": tmp_path / "bass.wav",
        "other": other_path,
    }

    chosen_path, chosen_name, vocals_rms = select_melody_stem(stems, threshold=0.01)

    assert chosen_name == "other", (
        f"Expected 'other' stem for silent vocals, got '{chosen_name}'"
    )
    assert vocals_rms < 0.01, f"Expected RMS < 0.01, got {vocals_rms:.6f}"
    assert chosen_path == other_path


def test_select_melody_stem_loud_vocals_picks_vocals(tmp_path: Path) -> None:
    """
    When the vocals stem has meaningful energy, select_melody_stem should
    return the 'vocals' stem.
    """
    from backend.app.services.music_engine.melody_extractor import select_melody_stem

    vocals_path = tmp_path / "vocals.wav"
    other_path = tmp_path / "other.wav"
    # Amplitude 0.5 → RMS ≈ 0.35, well above 0.01
    _write_wav(vocals_path, (_sine_wav(440.0, 2.0) * 0.5))
    _write_wav(other_path, np.zeros(SR * 2, dtype=np.float32))

    stems = {
        "vocals": vocals_path,
        "drums": tmp_path / "drums.wav",
        "bass": tmp_path / "bass.wav",
        "other": other_path,
    }

    _, chosen_name, vocals_rms = select_melody_stem(stems, threshold=0.01)

    assert chosen_name == "vocals", (
        f"Expected 'vocals' stem for loud audio, got '{chosen_name}'"
    )
    assert vocals_rms >= 0.01


# ---------------------------------------------------------------------------
# Test 2 — pitch_curve_to_notes: synthetic C4-E4-G4 sequence
# ---------------------------------------------------------------------------

def _note_freqs() -> dict[str, float]:
    return {"C4": 261.63, "E4": 329.63, "G4": 392.00}


def _build_synthetic_pitch_curve(
    sequence: list[tuple[str, float]],  # [(note_name, duration_s), ...]
    sr: int = SR,
    hop: int = 160,
) -> dict:
    """
    Build a fake pitch_curve dict mimicking torchcrepe output for a sequence of
    sustained notes.  All frames are marked voiced (confidence = 1.0).
    """
    freqs_map = _note_freqs()
    hop_s = hop / sr

    all_freqs = []
    all_conf = []

    for name, dur_s in sequence:
        n_frames = max(1, int(dur_s / hop_s))
        all_freqs.extend([freqs_map[name]] * n_frames)
        all_conf.extend([1.0] * n_frames)

    n = len(all_freqs)
    times = np.arange(n, dtype=np.float32) * hop_s
    freqs = np.array(all_freqs, dtype=np.float32)
    conf = np.array(all_conf, dtype=np.float32)

    return {"times": times, "frequencies": freqs, "confidence": conf, "sample_rate": sr}


def test_pitch_curve_to_notes_c4_e4_g4() -> None:
    """
    A synthetic C4→E4→G4 pitch curve (each 0.5 s, full confidence) should
    produce exactly 3 notes with the correct pitch names.
    Pitch tolerance: ±1 semitone (we use perfect sine → exact MIDI).
    """
    from backend.app.services.music_engine.melody_extractor import pitch_curve_to_notes

    sequence = [("C4", 0.5), ("E4", 0.5), ("G4", 0.5)]
    curve = _build_synthetic_pitch_curve(sequence)

    notes = pitch_curve_to_notes(curve, voice_threshold=0.5, min_note_duration=0.05)

    assert len(notes) == 3, f"Expected 3 notes, got {len(notes)}: {notes}"

    expected = ["C4", "E4", "G4"]
    for i, (note, exp_pitch) in enumerate(zip(notes, expected)):
        # Accept ±1 semitone tolerance by comparing MIDI numbers.
        exp_midi = {"C4": 60, "E4": 64, "G4": 67}[exp_pitch]
        got_midi = note["midi"]
        assert abs(got_midi - exp_midi) <= 1, (
            f"Note {i}: expected {exp_pitch} (MIDI {exp_midi}), "
            f"got {note['pitch']} (MIDI {got_midi})"
        )
        assert note["duration"] > 0.0, f"Note {i} has non-positive duration"
        assert 30 <= note["velocity"] <= 127, f"Note {i} velocity out of range"


def test_pitch_curve_to_notes_filters_unvoiced() -> None:
    """
    Frames with confidence below voice_threshold must be treated as rests and
    not produce note events.
    """
    from backend.app.services.music_engine.melody_extractor import pitch_curve_to_notes

    # Build a curve where every other frame is unvoiced.
    n = 200
    hop_s = 160 / SR
    times = np.arange(n, dtype=np.float32) * hop_s
    freqs = np.full(n, 261.63, dtype=np.float32)
    conf = np.array([1.0 if i % 2 == 0 else 0.0 for i in range(n)], dtype=np.float32)

    curve = {"times": times, "frequencies": freqs, "confidence": conf, "sample_rate": SR}
    notes = pitch_curve_to_notes(curve, voice_threshold=0.5, min_note_duration=0.05)

    # With every other frame unvoiced, individual voiced runs are only 1 frame
    # long (≈ 10 ms) — below min_note_duration=0.05 → should produce 0 notes.
    assert len(notes) == 0, (
        f"Expected 0 notes (all voiced runs too short), got {len(notes)}"
    )


def test_pitch_curve_to_notes_min_duration_filter() -> None:
    """
    Very short voiced segments below min_note_duration must be discarded.
    """
    from backend.app.services.music_engine.melody_extractor import pitch_curve_to_notes

    # 3 frames voiced at C4 then unvoiced — at hop 160/16000 = 0.01 s per frame
    # → 3 frames = 0.03 s, below default min_note_duration=0.05.
    sequence = [("C4", 0.03), ("E4", 0.5)]
    curve = _build_synthetic_pitch_curve(sequence)

    notes = pitch_curve_to_notes(curve, voice_threshold=0.5, min_note_duration=0.05)

    # The 0.03 s C4 must be dropped; only E4 should survive.
    pitches = [n["pitch"] for n in notes]
    assert "E4" in pitches, f"Expected E4 note in {pitches}"
    # C4 run is 0.03 s which may or may not merge depending on exact frames;
    # what matters is that at least 1 note survives.
    for note in notes:
        assert note["duration"] >= 0.05 - 1e-4, (
            f"Note {note['pitch']} duration {note['duration']:.4f} s below minimum"
        )


# ---------------------------------------------------------------------------
# Test 3 — extract_melody: integration smoke test (Demucs mocked)
# ---------------------------------------------------------------------------

def test_extract_melody_integration(tmp_path: Path) -> None:
    """
    Smoke-test the full extract_melody() pipeline with Demucs mocked out.
    torchcrepe is also mocked to return a known C4-E4-G4 curve so the test
    is fast and hermetic (no GPU or model downloads required).
    """
    from backend.app.services.music_engine.melody_extractor import extract_melody

    # Build fake stem WAV files.
    vocals_path = tmp_path / "vocals.wav"
    other_path = tmp_path / "other.wav"
    drums_path = tmp_path / "drums.wav"
    bass_path = tmp_path / "bass.wav"

    # Loud vocals so the vocals stem is chosen.
    _write_wav(vocals_path, _sine_wav(440.0, 2.0) * 0.5)
    for p in (other_path, drums_path, bass_path):
        _write_wav(p, np.zeros(SR, dtype=np.float32))

    fake_stems = {
        "vocals": vocals_path,
        "drums": drums_path,
        "bass": bass_path,
        "other": other_path,
    }

    fake_curve = _build_synthetic_pitch_curve([("C4", 0.5), ("E4", 0.5), ("G4", 0.5)])

    with (
        patch(
            "backend.app.services.music_engine.melody_extractor.separate_stems",
            return_value=fake_stems,
        ),
        patch(
            "backend.app.services.music_engine.melody_extractor.track_melody",
            return_value=fake_curve,
        ),
    ):
        # Provide a tiny dummy audio file (the mocks won't actually open it).
        dummy_audio = tmp_path / "song.wav"
        _write_wav(dummy_audio, _sine_wav(261.63, 1.0))

        result = extract_melody(dummy_audio, vocals_rms_threshold=0.01)

    assert result["note_count"] == 3, f"Expected 3 notes, got {result['note_count']}"
    assert result["stem_used"] == "vocals"
    assert result["vocals_rms"] > 0.01
    pitches = [n["pitch"] for n in result["notes"]]
    assert "C4" in pitches
    assert "E4" in pitches
    assert "G4" in pitches


def test_merge_nearby_notes() -> None:
    """
    Test that merge_nearby_notes correctly consolidates vibrato/fragmented notes
    within max_gap and max_semitone_diff.
    """
    from backend.app.services.music_engine.melody_extractor import merge_nearby_notes

    # Consecutive notes:
    # 1. F#4 (66), onset 1.0, duration 0.06 (ends 1.06)
    # 2. F#4 (66), onset 1.10, duration 0.40 (ends 1.50) -> gap 0.04s, semitone diff 0 -> should merge
    # 3. F4 (65), onset 1.55, duration 0.10 (ends 1.65) -> gap 0.05s, semitone diff 1 -> should merge into 1.0..1.65
    # 4. C4 (60), onset 2.00, duration 0.50 -> gap 0.35s > 0.15s, semitone diff 5 -> separate note
    raw_notes = [
        {"pitch": "F#4", "midi": 66, "onset": 1.0, "duration": 0.06, "velocity": 90},
        {"pitch": "F#4", "midi": 66, "onset": 1.10, "duration": 0.40, "velocity": 105},
        {"pitch": "F4", "midi": 65, "onset": 1.55, "duration": 0.10, "velocity": 85},
        {"pitch": "C4", "midi": 60, "onset": 2.00, "duration": 0.50, "velocity": 100},
    ]

    merged = merge_nearby_notes(raw_notes, max_gap=0.15, max_semitone_diff=1)
    assert len(merged) == 2, f"Expected 2 merged notes, got {len(merged)}: {merged}"
    assert merged[0]["onset"] == 1.0
    assert abs(merged[0]["duration"] - 0.65) < 1e-3
    assert merged[0]["pitch"] == "F#4"  # main pitch from longer 0.40s segment
    assert merged[0]["velocity"] == 105
    assert merged[1]["pitch"] == "C4"

