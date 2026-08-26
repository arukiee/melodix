"""
End-to-End Practice Scoring Integration Test
============================================

Simulates the complete client-to-backend flow:
1. Synthesizes test performance audio (WAV)
2. Submits WAV + target BPM + expected events to FastAPI POST /api/v1/practice/analyze
3. Verifies response payload structures and asserts correct scores under the gated scoring engine.
"""

import io
import os
import sys
import json
import uuid
import numpy as np
import soundfile as sf
import pretty_midi
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from app.factory import create_app
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User

app = create_app()

# Mock current user dependency
mock_user = User(
    id=uuid.uuid4(),
    email="integration_student@melodix.com",
    full_name="Integration Student",
    role="STUDENT",
    is_active=True
)

app.dependency_overrides[get_current_user] = lambda: mock_user
# Use dummy mock DB dependency to avoid real db dependency issues in auth/deps
app.dependency_overrides[get_db] = lambda: MagicMock()

client = TestClient(app)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def synthesize_performance_wav(notes: list, sr: int = 22050) -> bytes:
    """
    Synthesizes notes as clean sine waves to avoid long overlapping decay tails.
    """
    max_time = max(n["end"] for n in notes) if notes else 1.0
    total_samples = int(sr * (max_time + 0.5))
    audio = np.zeros(total_samples, dtype=np.float32)
    
    for n in notes:
        # MIDI to frequency
        freq = 440.0 * (2.0 ** ((n["pitch"] - 69.0) / 12.0))
        start_idx = int(sr * n["start"])
        end_idx = int(sr * n["end"])
        t = np.arange(end_idx - start_idx) / sr
        wave_data = 0.5 * np.sin(2 * np.pi * freq * t)
        
        # Simple fade to avoid clicking
        fade_len = min(100, len(wave_data) // 10)
        if fade_len > 0:
            wave_data[:fade_len] *= np.linspace(0.0, 1.0, fade_len)
            wave_data[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)
            
        audio[start_idx:end_idx] = wave_data
        
    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()

# ─────────────────────────────────────────────────────────────────────────────
# Test Scenarios
# ─────────────────────────────────────────────────────────────────────────────

class TestPracticeFlowIntegration:
    TARGET_BPM = 120
    
    # Expected Note Sequence: C4 (60) @ 0.0s, E4 (64) @ 0.5s, G4 (67) @ 1.0s (durations: 0.4s)
    EXPECTED_EVENTS = [
        {"note": "C4", "relative_time": 0.0, "duration": 0.4},
        {"note": "E4", "relative_time": 0.5, "duration": 0.4},
        {"note": "G4", "relative_time": 1.0, "duration": 0.4},
    ]

    def _analyze(self, wav_bytes: bytes) -> dict:
        resp = client.post(
            "/api/v1/practice/analyze",
            files={"file": ("performance.wav", io.BytesIO(wav_bytes), "audio/wav")},
            data={
                "target_bpm": str(self.TARGET_BPM),
                "expected_events": json.dumps(self.EXPECTED_EVENTS)
            }
        )
        assert resp.status_code == 200, f"Analysis failed: {resp.text}"
        return resp.json()

    def _print_results(self, label: str, data: dict):
        print("\n" + "="*80)
        print(f"INTEGRATION FLOW: {label}")
        print("="*80)
        print(f"Overall Score   : {data['scores']['overallScore']}")
        print(f"Pitch Score     : {data['scores']['pitchScore']}")
        print(f"Rhythm Score    : {data['scores']['rhythmScore']}")
        print(f"Duration Score  : {data['scores']['durationScore']}")
        print("Per-Note Comparison Results:")
        for item in data["note_comparison"]:
            played_note = item['played_note'] or '—'
            played_time_str = f"{item['played_time']:.2f}s" if item['played_time'] is not None else '—'
            timing_delta_str = f"{item['timing_delta_ms']}ms" if item['timing_delta_ms'] is not None else '—'
            print(f"  Expected: {item['expected_note']:<4} @ {item['expected_time']:.2f}s "
                  f"| Played: {played_note:<4} @ {played_time_str:<7} "
                  f"| Result: {item['result']:<8} "
                  f"| Timing Delta: {timing_delta_str}")

    def test_correct_performance(self, capsys):
        """1. Correct performance (all pitches, durations, and timing matching expected)."""
        notes = [
            {"pitch": 60, "start": 0.0, "end": 0.4},  # C4
            {"pitch": 64, "start": 0.5, "end": 0.9},  # E4
            {"pitch": 67, "start": 1.0, "end": 1.4},  # G4
        ]
        wav = synthesize_performance_wav(notes)
        data = self._analyze(wav)
        
        with capsys.disabled():
            self._print_results("1. CORRECT PERFORMANCE", data)

        # Perfect performance must score >= 94.0
        assert data["scores"]["overallScore"] >= 94.0

    def test_wrong_note_performance(self, capsys):
        """2. Wrong-note performance (plays C4 @ 0.0s, F4 (wrong) @ 0.5s, G4 @ 1.0s)."""
        notes = [
            {"pitch": 60, "start": 0.0, "end": 0.4},  # C4
            {"pitch": 65, "start": 0.5, "end": 0.9},  # F4 (wrong)
            {"pitch": 67, "start": 1.0, "end": 1.4},  # G4
        ]
        wav = synthesize_performance_wav(notes)
        data = self._analyze(wav)
        
        with capsys.disabled():
            self._print_results("2. WRONG-NOTE PERFORMANCE", data)

        # Wrong note must reduce pitch score and overall score significantly (gated)
        assert data["scores"]["overallScore"] < 80.0
        # F4 was wrong note
        assert any(x["result"] == "wrong" for x in data["note_comparison"])

    def test_missed_note_performance(self, capsys):
        """3. Missed-note performance (plays C4 @ 0.0s, E4 missed, G4 @ 1.0s)."""
        notes = [
            {"pitch": 60, "start": 0.0, "end": 0.4},  # C4
            # E4 is missing
            {"pitch": 67, "start": 1.0, "end": 1.4},  # G4
        ]
        wav = synthesize_performance_wav(notes)
        data = self._analyze(wav)
        
        with capsys.disabled():
            self._print_results("3. MISSED-NOTE PERFORMANCE", data)

        assert data["scores"]["overallScore"] < 80.0
        assert any(x["result"] == "missed" for x in data["note_comparison"])

    def test_early_late_performance(self, capsys):
        """4. Early/late performance (C4 perfectly on time, E4 played late by 100ms, G4 late by 300ms)."""
        notes = [
            {"pitch": 60, "start": 0.0, "end": 0.4},
            {"pitch": 64, "start": 0.600, "end": 1.0},  # 100ms late
            {"pitch": 67, "start": 1.300, "end": 1.7},  # 300ms late
        ]
        wav = synthesize_performance_wav(notes)
        data = self._analyze(wav)
        
        with capsys.disabled():
            self._print_results("4. EARLY/LATE PERFORMANCE", data)

        # Rhythm score should drop, reducing overall score compared to perfect execution
        assert data["scores"]["overallScore"] < 95.0
