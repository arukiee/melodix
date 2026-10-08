"""Export a measured checkpoint for deployment."""

import argparse
import shutil
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--checkpoint", default="ml/checkpoints/best.pt")
parser.add_argument("--output", default="ml/checkpoints/deployed.pt")
args = parser.parse_args()
source = Path(args.checkpoint)
if not source.exists():
    raise SystemExit("No trained checkpoint exists; train and evaluate before export")
Path(args.output).parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(source, args.output)
print(f"exported {source} to {args.output}")