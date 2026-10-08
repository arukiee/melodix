"""Shared checkpoint-backed inference for offline and FastAPI paths."""

import time
from pathlib import Path

import numpy as np

from ml.data.preprocessing import AudioConfig, log_mel_spectrogram
from ml.models.transcription.postprocess import probabilities_to_notes


class Transcriber:
    def __init__(self, checkpoint_path: str | Path, config: dict, device: str = "cpu") -> None:
        try:
            import torch
            from ml.models.transcription.cnn_bilstm import FrequencyAwareCNNBiLSTM
        except ImportError as exc:
            raise RuntimeError("Install ml/requirements.txt for model inference") from exc
        self.torch = torch
        self.config = config
        self.device = torch.device(device)
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.model = FrequencyAwareCNNBiLSTM(frequency_bins=int(config["n_mels"])).to(self.device)
        self.model.load_state_dict(checkpoint["model"])
        self.model.eval()
        self.version = checkpoint.get("experiment_id", config.get("experiment_id", "unknown"))
        self.audio_config = AudioConfig(config["sample_rate"], config["n_fft"], config["hop_length"], config["n_mels"], config["f_min"], config["f_max"])

    def transcribe(self, audio: np.ndarray) -> tuple[list[dict], float]:
        started = time.perf_counter()
        features = log_mel_spectrogram(audio, self.audio_config)
        tensor = self.torch.from_numpy(features.T[None, None]).to(self.device)
        with self.torch.no_grad():
            output = self.model(tensor)
        notes = probabilities_to_notes(output, self.audio_config.hop_length * 1000 / self.audio_config.sample_rate, self.config["onset_threshold"], self.config["frame_threshold"], self.config["offset_threshold"])
        return notes, (time.perf_counter() - started) * 1000
