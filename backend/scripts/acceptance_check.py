from pathlib import Path
import json
import sys
import subprocess
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import time

from basic_pitch.inference import predict

from app.services.music_engine.melody_processor import clean_melody_events, melody_payload
from app.services.music_engine.source_separator import separate_audio


def scalar(value):
    while isinstance(value, (list, tuple)):
        value = value[0] if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def main():
    cases = [
        ("vocal", "ytsearch1:Adele Hello official audio"),
        ("instrumental", "ytsearch1:Bach Prelude C Major piano instrumental"),
    ]
    root = Path(tempfile.mkdtemp(prefix="melodix-acceptance-"))
    print(f"acceptance root: {root}", flush=True)
    summary = []

    for label, query in cases:
        case_dir = root / label
        case_dir.mkdir()
        target = case_dir / "source.%(ext)s"
        subprocess.run(
            [
                "./venv311/bin/yt-dlp",
                "--no-playlist",
                "-x",
                "--audio-format",
                "wav",
                "--audio-quality",
                "5",
                "-o",
                str(target),
                query,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"{label}: download done", flush=True)
        source = next(case_dir.glob("source.*"))
        stem = "vocals" if label == "vocal" else "other"
        stem_path = separate_audio(str(source), str(case_dir / "stems"), stem)
        print(f"{label}: separation done ({stem})", flush=True)
        _, _, raw_events = predict(
            stem_path,
            onset_threshold=0.5,
            frame_threshold=0.3,
            minimum_note_length=50.0,
            minimum_frequency=80.0,
            maximum_frequency=3000.0,
        )
        print(f"{label}: transcription done ({len(raw_events)} raw events)", flush=True)
        raw = [
            (
                float(event[0]),
                float(event[1]),
                int(event[2]),
                int(event[3]),
                scalar(event[4]) if len(event) > 4 else 0.0,
            )
            for event in raw_events
        ]
        cleaned = clean_melody_events(raw, stem_path)
        payload = melody_payload(cleaned)
        overlaps = sum(
            1 for left, right in zip(cleaned, cleaned[1:]) if left[1] > right[0]
        )
        summary.append(
            {
                "case": label,
                "source": source.name,
                "stem": stem,
                "raw_notes": len(raw),
                "clean_notes": len(cleaned),
                "overlap_count": overlaps,
                "first_notes": payload[:8],
            }
        )
        print(f"{label}: cleanup done ({len(cleaned)} melody notes)", flush=True)

    print(json.dumps({"root": str(root), "cases": summary}, indent=2), flush=True)


if __name__ == "__main__":
    main()
