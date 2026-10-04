"""Versioned, atomic local save storage for trusted Flip-owned state."""

from __future__ import annotations

import json
import os
from pathlib import Path


SAVE_VERSION = 1


def default_save_path() -> Path:
    if os.name == "nt" and os.environ.get("APPDATA"):
        root = Path(os.environ["APPDATA"])
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / "VoidEcosystem" / "flip-profile.json"


class ProfileStore:
    def __init__(self, path: Path | None = None):
        self.path = path or default_save_path()
        self.last_error: str | None = None

    def load(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if payload.get("version") != SAVE_VERSION:
                self.last_error = "Unsupported save version; defaults loaded."
                return {}
            return payload
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
            self.last_error = f"Save could not be loaded: {error}"
            return {}

    def save(self, payload: dict) -> bool:
        data = {"version": SAVE_VERSION, **payload}
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
            temporary.replace(self.path)
            self.last_error = None
            return True
        except OSError as error:
            self.last_error = f"Save could not be written: {error}"
            return False
