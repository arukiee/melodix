"""Fixed-window manifest dataset with training-only deterministic augmentation."""

import csv
from pathlib import Path

import numpy as np

from ml.data.preprocessing import AudioConfig, log_mel_spectrogram, midi_labels


class ManifestDataset:
    def __init__(self, manifest: Path, config: dict, split: str) -> None:
        self.config = config
        with manifest.open(newline="") as stream:
            self.records = [row for row in csv.DictReader(stream) if row["split"] == split]
        self.audio = AudioConfig(config["sample_rate"], config["n_fft"], config["hop_length"], config["n_mels"], config["f_min"], config["f_max"])
        self.segment_frames = int(config["segment_seconds"] * config["sample_rate"] / config["hop_length"])
        self.training = split == "train"

    def __len__(self):
        return len(self.records)

    def __getitem__(self, index):
        try:
            import soundfile as sf
            import torch
        except ImportError as exc:
            raise RuntimeError("Install ml/requirements.txt before loading audio") from exc
        record = self.records[index]
        samples, source_rate = sf.read(record["audio_path"], dtype="float32", always_2d=False)
        if samples.ndim > 1:
            samples = samples.mean(axis=1)
        if source_rate != self.audio.sample_rate:
            import librosa
            samples = librosa.resample(samples, orig_sr=source_rate, target_sr=self.audio.sample_rate)
        if self.training and self.config.get("augmentation", {}).get("enabled"):
            samples = samples * (10 ** (np.random.uniform(-6, 6) / 20))
            noise = np.random.normal(0, max(1e-5, np.std(samples) / 10), size=samples.shape).astype("float32")
            samples = samples + noise
        features = log_mel_spectrogram(samples, self.audio)
        features = features[:, :self.segment_frames]
        if features.shape[1] < self.segment_frames:
            features = np.pad(features, ((0, 0), (0, self.segment_frames - features.shape[1])))
        labels = midi_labels(record["midi_path"], self.segment_frames, self.audio)
        return torch.from_numpy(features.T[None]), {key: torch.from_numpy(value) for key, value in labels.items()}


class SyntheticSmokeDataset:
    """Tiny deterministic tensor dataset for checking one training epoch in CI."""

    def __init__(self, config: dict, size: int = 2) -> None:
        import torch
        generator = torch.Generator().manual_seed(int(config["seed"]))
        frames = int(config["segment_seconds"] * config["sample_rate"] / config["hop_length"])
        self.features = torch.randn(size, 1, frames, int(config["n_mels"]), generator=generator)
        self.labels = {name: torch.randint(0, 2, (size, frames, 88), generator=generator).float() for name in ("onset", "frame", "offset")}
        self.labels["velocity"] = torch.rand(size, frames, 88, generator=generator)

    def __len__(self):
        return len(self.features)

    def __getitem__(self, index):
        return self.features[index], {key: value[index] for key, value in self.labels.items()}