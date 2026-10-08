"""Validate a checkpoint against the validation split."""

import argparse
import yaml
import torch
from torch.utils.data import DataLoader

from ml.models.transcription.cnn_bilstm import FrequencyAwareCNNBiLSTM
from ml.training.dataset import ManifestDataset
from ml.training.validation import validate_model


parser = argparse.ArgumentParser()
parser.add_argument("--manifest", required=True)
parser.add_argument("--checkpoint", default="ml/checkpoints/best.pt")
parser.add_argument("--config", default="ml/configs/transcription.yaml")
args = parser.parse_args()
config = yaml.safe_load(open(args.config))
checkpoint = torch.load(args.checkpoint, map_location="cpu")
model = FrequencyAwareCNNBiLSTM(frequency_bins=config["n_mels"])
model.load_state_dict(checkpoint["model"])
metrics = validate_model(model, DataLoader(ManifestDataset(args.manifest, config, "validation"), batch_size=config["batch_size"]), "cpu", config)
print(metrics)