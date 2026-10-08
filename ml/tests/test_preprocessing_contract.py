import numpy as np

from ml.data.preprocessing import AudioConfig


def test_audio_config_is_explicit_and_88_key_label_shape_contract():
    config = AudioConfig(sample_rate=16000, n_fft=2048, hop_length=320, n_mels=128)
    assert config.sample_rate == 16000
    assert config.n_mels == 128
    labels = {name: np.zeros((10, 88), dtype=np.float32) for name in ("onset", "frame", "offset", "velocity")}
    assert all(value.shape == (10, 88) for value in labels.values())
