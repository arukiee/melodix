import pytest
import sys
from unittest.mock import MagicMock
# Mock librosa before importing BPMDetector
sys.modules['librosa'] = MagicMock()
from app.services.music_engine.bpm_detector import BPMDetector
import numpy as np

def test_bpm_detector_confidence():
    detector = BPMDetector()
    
    # We can mock a simple audio array to test librosa behavior, 
    # but for unit testing the logic itself, we verify it handles edge cases correctly.
    
    # Empty audio array should return 0 bpm or raise
    empty_audio = np.array([])
    mock_db = MagicMock()
    audio_asset = MagicMock()
    detector._load_audio = MagicMock(return_value=(empty_audio, 22050))
    
    res = detector.detect(audio_asset, mock_db)
    
    assert res["tempo_bpm"] == 0.0
    assert res["confidence"] == 0.0

def test_bpm_detector_valid_audio():
    detector = BPMDetector()
    
    # Create a simple synthetic click track at ~120 BPM
    sr = 22050
    duration = 5 # seconds
    audio = np.zeros(sr * duration)
    # 120 BPM = 2 beats per second = 1 beat every sr/2 samples
    for i in range(0, len(audio), sr // 2):
        audio[i:i+100] = 1.0 # click
        
    # Mock the behavior of librosa inside the detector
    import librosa
    librosa.beat.beat_track.return_value = (120.0, np.array([0.5, 1.0, 1.5]))
    
    mock_db = MagicMock()
    # the signature is detect(self, audio_asset: AudioAsset, db: Session)
    # we need to mock the audio asset loading too
    audio_asset = MagicMock()
    audio_asset.storage_path = "mock/path"
    
    # We actually just want to test the detect_bpm logic if possible, 
    # but the method is detect(audio_asset, db). It loads from minio.
    # So the unit test as written is trying to test internal logic.
    # Let's mock _load_audio.
    detector._load_audio = MagicMock(return_value=(audio, sr))
    
    res = detector.detect(audio_asset, mock_db)
    
    assert res["tempo_bpm"] == 120.0
    assert res["confidence"] > 0.0
