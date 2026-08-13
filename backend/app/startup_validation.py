# backend/app/startup_validation.py
"""Validate that environment files are in sync.

The project uses two environment files:
- `.env` (developer local defaults)
- `.env.docker` (Docker Compose runtime)

Only network‑specific variables should differ. All other values – especially
OAuth configuration – must be identical. This script checks a whitelist of
variables and raises an exception if any mismatch is found, preventing the
application from starting with drifted configuration.
"""

import os
from pathlib import Path

# List of variables that must be identical between .env and .env.docker
SYNC_VARS = [
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REDIRECT_URI",
    # Add other shared vars here if the project grows
]

def _load_env(file_path: Path) -> dict:
    """Parse a simple KEY=VALUE file (ignoring comments and empty lines)."""
    env = {}
    if not file_path.is_file():
        return env
    for line in file_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env

def validate_env_sync(project_root: Path = Path(__file__).parents[2]) -> None:
    """Compare .env and .env.docker for the variables in ``SYNC_VARS``.

    Raises
    ------
    RuntimeError
        If any of the synchronized variables differ between the two files.
    """
    env_path = project_root / ".env"
    docker_env_path = project_root / ".env.docker"

    env = _load_env(env_path)
    docker_env = _load_env(docker_env_path)

    mismatches = [var for var in SYNC_VARS if env.get(var) != docker_env.get(var)]
    if mismatches:
        details = [
            f"{var}: .env='{env.get(var)}' vs .env.docker='{docker_env.get(var)}'"
            for var in mismatches
        ]
        raise RuntimeError(
            "Configuration drift detected for synchronized variables:\n"
            + "\n".join(details)
            + "\nEnsure .env and .env.docker contain identical values for these keys."
        )

# If this module is imported directly (e.g., via ``python -m backend.app.startup_validation``)
# we execute the validation immediately so developers can run a quick check.
if __name__ == "__main__":
    try:
        validate_env_sync()
        print("✅ Environment files are in sync.")
    except RuntimeError as exc:
        print(str(exc))
        raise
