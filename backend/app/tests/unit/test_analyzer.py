import numpy as np
import pytest
from app.services.music_engine.base_analyzer import AnalysisRequest, ExpectedEvent
from app.services.music_engine.analyzer import AutocorrelationAnalyzer, hz_to_note_and_cents, detect_pitch_autocorrelation
from app.services.ai_coach.coaching_service import AICoachingService

def test_hz_to_note_and_cents():
    note, cents = hz_to_note_and_cents(440.0)
    assert note == "A4"
    assert abs(cents) < 0.1

    note, cents = hz_to_note_and_cents(261.63)
    assert note == "C4"

def test_pitch_detection_sine_wave():
    sr = 16000
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    signal = 0.5 * np.sin(2 * np.pi * 440.0 * t)

    f0 = detect_pitch_autocorrelation(signal, sr)
    assert abs(f0 - 440.0) < 5.0

def test_autocorrelation_analyzer_wrong_event():
    sr = 16000
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    signal = 0.5 * np.sin(2 * np.pi * 440.0 * t) # A4

    analyzer = AutocorrelationAnalyzer()
    req = AnalysisRequest(
        audio_data=signal,
        sample_rate=sr,
        expected_events=[ExpectedEvent(note="C4", relative_time=0.0, duration=0.5)],
        target_bpm=60
    )

    res = analyzer.analyze(req)
    assert res.scores.pitchScore < 100.0
    assert len(res.mistakes) >= 1
    assert any(m.type == "missed_note" for m in res.mistakes)

@pytest.mark.asyncio
async def test_ai_coaching_fallback():
    analyzer = AutocorrelationAnalyzer()
    sr = 16000
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    signal = 0.5 * np.sin(2 * np.pi * 440.0 * t) # A4
    
    req = AnalysisRequest(
        audio_data=signal,
        sample_rate=sr,
        expected_events=[ExpectedEvent(note="A4", relative_time=0.0, duration=0.5)],
        target_bpm=60
    )
    res = analyzer.analyze(req)
    
    # Test coaching service output
    feedback = await AICoachingService.generate_coaching(
        song_title="Twinkle",
        scores=res.scores,
        tempo_metrics=res.tempo_metrics,
        mistakes=res.mistakes,
        measure_scores=res.measure_scores
    )
    
    assert feedback.summary != ""
    assert len(feedback.strengths) > 0
    assert feedback.nextGoal != ""
