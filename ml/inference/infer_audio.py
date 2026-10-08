"""Run the same custom checkpoint inference used by the ML service."""

import argparse
import json
from pathlib import Path

import librosa
import yaml

from ml.inference.transcriber import Transcriber


parser = argparse.ArgumentParser()
parser.add_argument("audio", type=Path)
parser.add_argument("--checkpoint", default="ml/checkpoints/best.pt")
parser.add_argument("--config", default="ml/configs/transcription.yaml")
parser.add_argument("--output", type=Path)
args = parser.parse_args()
config = yaml.safe_load(Path(args.config).read_text())
audio, _ = librosa.load(args.audio, sr=config["sample_rate"], mono=True)
transcriber = Transcriber(args.checkpoint, config)
notes, latency = transcriber.transcribe(audio)
result = {"model_version": transcriber.version, "inference_latency_ms": latency, "notes": notes}
if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))