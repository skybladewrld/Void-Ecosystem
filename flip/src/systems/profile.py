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
    weekly_key: str = ""
    weekly_quests: list[dict] = field(default_factory=list)
    current_streak: int = 0
    longest_streak: int = 0
    last_daily_completion: str = ""
    mastery: dict = field(default_factory=dict)
    completed_challenges: list[str] = field(default_factory=list)
    codex: dict = field(default_factory=dict)
    completed_achievements: list[str] = field(default_factory=list)
    notification_history: list[dict] = field(default_factory=list)
    profile_stats: dict = field(default_factory=dict)
    behavior: dict = field(default_factory=dict)
    display_name: str = "PLAYER"

    def __post_init__(self) -> None:
        self.game_stats.setdefault("void_merge_high_score", 0)
        self.game_stats.setdefault("void_merge_runs", 0)
        self.game_stats.setdefault("signal_serpent_high_score", 0)
        self.game_stats.setdefault("signal_serpent_highest_length", 3)
        self.game_stats.setdefault("signal_serpent_best_combo", 1)
        self.game_stats.setdefault("signal_serpent_total_runs", 0)
        self.game_stats.setdefault("blackglass_wins", 0)
        self.game_stats.setdefault("blackglass_losses", 0)
        self.game_stats.setdefault("blackglass_local_matches", 0)
        self.game_stats.setdefault("blackglass_best_captures", 0)
        self.profile_stats.setdefault("purchases", 0)
        self.profile_stats.setdefault("explores", 0)
        self.profile_stats.setdefault("crafted", 0)
        self.profile_stats.setdefault("care_actions", 0)
        self.profile_stats.setdefault("playtime_seconds", 0)

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
            weekly_key=str(core.get("weekly_key", "")),
            weekly_quests=list(core.get("weekly_quests", []))[:2],
            current_streak=max(0, int(core.get("current_streak", 0))),
            longest_streak=max(0, int(core.get("longest_streak", 0))),
            last_daily_completion=str(core.get("last_daily_completion", "")),
            mastery=dict(core.get("mastery", {})),
            completed_challenges=list(core.get("completed_challenges", [])),
            codex=dict(core.get("codex", {})),
            completed_achievements=list(core.get("completed_achievements", [])),
            notification_history=list(core.get("notification_history", []))[-20:],
            profile_stats=dict(core.get("profile_stats", {})),
            behavior=dict(core.get("behavior", {})),
            display_name=str(core.get("display_name", "PLAYER"))[:18] or "PLAYER",
        )
        legacy_achievements = [reward.split(":", 1)[1] for reward in profile.claimed_rewards if reward.startswith("achievement:")]
        profile.completed_achievements = list(dict.fromkeys(profile.completed_achievements + legacy_achievements))
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
                "weekly_key": self.weekly_key,
                "weekly_quests": self.weekly_quests,
                "current_streak": self.current_streak,
                "longest_streak": self.longest_streak,
                "last_daily_completion": self.last_daily_completion,
                "mastery": self.mastery,
                "completed_challenges": self.completed_challenges,
                "codex": self.codex,
                "completed_achievements": self.completed_achievements,
                "notification_history": self.notification_history[-20:],
                "profile_stats": self.profile_stats,
                "behavior": self.behavior,
                "display_name": self.display_name,
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
