"""Versioned, atomic local save storage for trusted Flip-owned state."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path


SAVE_VERSION = 3


def migrate_payload(payload: dict) -> dict:
    """Add Core Loop defaults while preserving every known v1 field."""

    version = int(payload.get("version", 1))
    if version > SAVE_VERSION:
        raise ValueError(f"Save version {version} is newer than supported version {SAVE_VERSION}.")
    migrated = dict(payload)
    if version < 2:
        migrated.setdefault("core", {
            "flux": 120,
            "quest_date": "",
            "quests": [],
            "activity": [],
            "seen_unlocks": [],
            "claimed_rewards": [],
        })
    if version < 3:
        if not isinstance(migrated.get("core"), dict):
            migrated["core"] = {}
        core = migrated["core"]
        defaults = {
            "weekly_key": "", "weekly_quests": [], "current_streak": 0,
            "longest_streak": 0, "last_daily_completion": "", "mastery": {},
            "completed_challenges": [], "codex": {}, "completed_achievements": [],
            "notification_history": [], "profile_stats": {}, "behavior": {},
            "display_name": "PLAYER",
        }
        for key, value in defaults.items():
            core.setdefault(key, value)
    migrated["version"] = SAVE_VERSION
    return migrated


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
            if not isinstance(payload, dict):
                raise ValueError("Save root must be an object.")
            return migrate_payload(payload)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
            self.last_error = f"Save could not be loaded: {error}"
            return {}

    def save(self, payload: dict) -> bool:
        data = {**payload, "version": SAVE_VERSION}
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.exists():
                shutil.copy2(self.path, self.path.with_suffix(self.path.suffix + ".bak"))
            temporary.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
            temporary.replace(self.path)
            self.last_error = None
            return True
        except OSError as error:
            self.last_error = f"Save could not be written: {error}"
            return False
