"""Demucs-backed source separation for transcription."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def choose_stem(original_filename: str | None) -> str:
    """Use vocals for songs and ``other`` for clearly instrumental files."""
    name = (original_filename or "").lower()
    markers = ("instrumental", "piano", "classical", "karaoke", "midi")
    return "other" if any(marker in name for marker in markers) else "vocals"


def separate_audio(audio_path: str, output_dir: str, stem: str) -> str:
    """Run Demucs and return the selected stem path."""
    if stem not in {"vocals", "other"}:
        raise ValueError(f"Unsupported transcription stem: {stem}")

    command = [sys.executable, "-m", "demucs", "-n", "htdemucs", "--out", output_dir, audio_path]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=900)
    except FileNotFoundError as exc:
        raise RuntimeError("Demucs is not installed. Install it with: pip install demucs") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace")[-1000:]
        raise RuntimeError(f"Demucs source separation failed: {detail}") from exc

    stem_path = Path(output_dir) / "htdemucs" / Path(audio_path).stem / f"{stem}.wav"
    if not stem_path.exists():
        raise RuntimeError(f"Demucs did not produce the expected {stem} stem: {stem_path}")
    return str(stem_path)