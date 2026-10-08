"""Final held-out evaluation; invoke only after model selection is complete."""

import argparse
import json
from pathlib import Path
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
parser.add_argument("--output", default="ml/reports/evaluation.json")
args = parser.parse_args()
config = yaml.safe_load(open(args.config))
checkpoint = torch.load(args.checkpoint, map_location="cpu")
model = FrequencyAwareCNNBiLSTM(frequency_bins=config["n_mels"])
model.load_state_dict(checkpoint["model"])
metrics = validate_model(model, DataLoader(ManifestDataset(args.manifest, config, "test"), batch_size=config["batch_size"]), "cpu", config)
Path(args.output).parent.mkdir(parents=True, exist_ok=True)
Path(args.output).write_text(json.dumps({"experiment_id": config["experiment_id"], "split": "test", "metrics": metrics}, indent=2))
print(metrics)