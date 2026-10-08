"""Build a MAESTRO manifest without copying or committing dataset files."""

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", default=Path("ml/data/manifests/maestro.csv"), type=Path)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--limit", type=int, help="Limit records per split for a smoke experiment")
    args = parser.parse_args()
    metadata = json.loads(args.metadata.read_text()) if args.metadata else {}
    records = []
    for midi_path in sorted(args.root.rglob("*.midi")) + sorted(args.root.rglob("*.mid")):
        audio_path = midi_path.with_suffix(".wav")
        if not audio_path.exists():
            continue
        record = metadata.get(midi_path.stem, {})
        records.append({
            "file_id": midi_path.stem, "audio_path": str(audio_path), "midi_path": str(midi_path),
            "split": record.get("split", "unknown"), "duration": record.get("duration", ""),
            "augmentation_applied": "none", "sample_rate": record.get("sample_rate", ""),
            "preprocessing_version": "logmel_v1", "dataset_version": "MAESTRO",
        })
    if args.limit:
        records = records[:args.limit]
    if not records:
        raise SystemExit("No paired MIDI/WAV files found")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    print(f"wrote {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()
