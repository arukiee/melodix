"""Configurable multi-head transcription loss."""

try:
    import torch
    from torch import nn
except ImportError as exc:  # pragma: no cover
    raise ImportError("Install ml/requirements.txt to use transcription losses") from exc


def transcription_loss(predictions: dict, labels: dict, config: dict) -> tuple:
    bce = nn.BCELoss()
    onset = bce(predictions["onset"], labels["onset"])
    frame = bce(predictions["frame"], labels["frame"])
    offset = bce(predictions["offset"], labels["offset"])
    velocity = nn.HuberLoss()(predictions["velocity"], labels["velocity"])
    total = (config["onset_weight"] * onset + config["frame_weight"] * frame +
             config["offset_weight"] * offset + config["velocity_weight"] * velocity)
    return total, {"onset": onset.item(), "frame": frame.item(), "offset": offset.item(), "velocity": velocity.item()}
