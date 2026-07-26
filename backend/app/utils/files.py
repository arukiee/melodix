"""File‑related utilities (path handling, temp files, etc.)."""

import os
from pathlib import Path

def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
