"""Frequency-aware multi-branch CNN-BiLSTM piano transcription model."""

try:
    import torch
    from torch import nn
except ImportError as exc:  # pragma: no cover - exercised when ML extras are absent
    raise ImportError("Install ml/requirements.txt to use the transcription model") from exc


class DepthwiseSeparableConv(nn.Module):
    def __init__(self, channels: int, output_channels: int) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv2d(channels, channels, 3, padding=1, groups=channels, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels, output_channels, 1, bias=False),
            nn.BatchNorm2d(output_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, inputs):
        return self.layers(inputs)


class FrequencyBranch(nn.Module):
    def __init__(self, output_channels: int = 32) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1, bias=False),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            DepthwiseSeparableConv(16, output_channels),
            nn.MaxPool2d((1, 2)),
            DepthwiseSeparableConv(output_channels, output_channels),
        )

    def forward(self, inputs):
        return self.layers(inputs)


class FrequencyAwareCNNBiLSTM(nn.Module):
    """Predict independent piano-key onset/frame/offset probabilities."""

    def __init__(self, frequency_bins: int = 128, hidden_size: int = 128, keys: int = 88) -> None:
        super().__init__()
        self.keys = keys
        self.low_branch = FrequencyBranch()
        self.mid_branch = FrequencyBranch()
        self.high_branch = FrequencyBranch()
        self.branch_pool = nn.AdaptiveAvgPool2d((None, 8))
        self.temporal = nn.LSTM(32 * 8 * 3, hidden_size, batch_first=True, bidirectional=True)
        self.onset_head = nn.Sequential(nn.Linear(hidden_size * 2, keys), nn.Sigmoid())
        self.frame_head = nn.Sequential(nn.Linear(hidden_size * 2, keys), nn.Sigmoid())
        self.offset_head = nn.Sequential(nn.Linear(hidden_size * 2, keys), nn.Sigmoid())
        self.velocity_head = nn.Sequential(nn.Linear(hidden_size * 2, keys), nn.Sigmoid())

    def forward(self, inputs):
        _, _, _, frequency_bins = inputs.shape
        low_end = max(1, frequency_bins // 3)
        mid_end = max(low_end + 1, 2 * frequency_bins // 3)
        bands = (
            self.low_branch(inputs[..., :low_end]),
            self.mid_branch(inputs[..., low_end:mid_end]),
            self.high_branch(inputs[..., mid_end:]),
        )
        features = torch.cat(tuple(self.branch_pool(band) for band in bands), dim=1)
        features = features.permute(0, 2, 1, 3).flatten(2)
        sequence, _ = self.temporal(features)
        return {
            "onset": self.onset_head(sequence),
            "frame": self.frame_head(sequence),
            "offset": self.offset_head(sequence),
            "velocity": self.velocity_head(sequence),
        }
