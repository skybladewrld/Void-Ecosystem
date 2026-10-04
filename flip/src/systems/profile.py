"""Serializable progression state introduced by the Core Loop update."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CoreProfile:
    flux: int = 120
    quest_date: str = ""
    quests: list[dict] = field(default_factory=list)
    activity: list[dict] = field(default_factory=list)
    seen_unlocks: list[str] = field(default_factory=list)
    claimed_rewards: list[str] = field(default_factory=list)
    game_stats: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.game_stats.setdefault("void_merge_high_score", 0)
        self.game_stats.setdefault("void_merge_runs", 0)
        self.game_stats.setdefault("signal_serpent_high_score", 0)
        self.game_stats.setdefault("signal_serpent_highest_length", 3)
        self.game_stats.setdefault("signal_serpent_best_combo", 1)
        self.game_stats.setdefault("signal_serpent_total_runs", 0)

    @classmethod
    def from_payload(cls, payload: dict) -> "CoreProfile":
        core = payload.get("core", {}) if isinstance(payload.get("core", {}), dict) else {}
        profile = cls(
            flux=max(0, int(core.get("flux", payload.get("flux", 120)))),
            quest_date=str(core.get("quest_date", payload.get("quest_date", ""))),
            quests=list(core.get("quests", payload.get("quests", [])))[:3],
            activity=list(core.get("activity", payload.get("activity", [])))[-75:],
            seen_unlocks=list(core.get("seen_unlocks", payload.get("unlocks", []))),
            claimed_rewards=list(core.get("claimed_rewards", []))[-100:],
            game_stats=dict(payload.get("game_stats", {})),
        )
        return profile

    def to_payload(self) -> dict:
        return {
            "core": {
                "flux": self.flux,
                "quest_date": self.quest_date,
                "quests": self.quests,
                "activity": self.activity[-75:],
                "seen_unlocks": self.seen_unlocks,
                "claimed_rewards": self.claimed_rewards[-100:],
            },
            "game_stats": self.game_stats,
        }

    def add_activity(self, kind: str, message: str, *, timestamp: datetime | None = None) -> None:
        timestamp = timestamp or datetime.now().astimezone()
        self.activity.append({
            "time": timestamp.isoformat(timespec="minutes"),
            "kind": kind,
            "message": str(message)[:100],
        })
        self.activity = self.activity[-75:]

    def remember_reward(self, reward_id: str) -> bool:
        """Return False when an already-applied reward is presented again."""

        if reward_id in self.claimed_rewards:
            return False
        self.claimed_rewards.append(reward_id)
        self.claimed_rewards = self.claimed_rewards[-100:]
        return True
