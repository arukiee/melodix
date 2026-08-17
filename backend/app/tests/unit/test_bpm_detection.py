import pytest
from app.services.music_engine.bpm_detector import BPMDetector
from unittest.mock import patch
import numpy as np

@patch('librosa.beat.beat_track')
@patch('librosa.onset.onset_strength')
@patch('librosa.frames_to_time')
def test_bpm_detection(mock_frames_to_time, mock_onset_strength, mock_beat_track):
    # Mock librosa behavior
    mock_onset_strength.return_value = np.array([0.1, 0.5, 0.2, 0.8, 0.1])
    mock_beat_track.return_value = (120.0, np.array([1, 3]))
    mock_frames_to_time.return_value = np.array([0.5, 1.5])
    
    detector = BPMDetector()
    # Dummy audio data
    audio_data = np.zeros(44100)
    
    result = detector.detect_bpm(audio_data, 22050)
    
    assert result.tempo_bpm == 120.0
    assert len(result.beat_times) == 2
    assert result.confidence >= 0.0 and result.confidence <= 1.0
    assert result.method == "librosa_beat_track"
