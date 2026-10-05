"""Persistent, non-spendable mastery and one-time game challenges."""

from __future__ import annotations

from dataclasses import dataclass


GAME_TITLES = {"void_merge": "VOID MERGE", "signal_serpent": "SIGNAL SERPENT", "blackglass": "BLACKGLASS"}


@dataclass(frozen=True)
class Challenge:
    challenge_id: str
    game_id: str
    title: str
    metric: str
    target: int
    mastery_xp: int = 30
    flux: int = 10


CHALLENGES = (
    Challenge("merge_512", "void_merge", "CORE 512", "highest_tile", 512),
    Challenge("merge_1024", "void_merge", "CORE 1024", "highest_tile", 1024, 50, 20),
    Challenge("merge_score_10k", "void_merge", "FIVE DIGITS", "score", 10000, 60, 25),
    Challenge("merge_ten", "void_merge", "CHAIN REACTION", "merges", 10),
    Challenge("serpent_length_20", "signal_serpent", "LONG SIGNAL", "length", 20),
    Challenge("serpent_combo_5", "signal_serpent", "FIVE PULSE", "best_combo", 5),
    Challenge("serpent_tier_5", "signal_serpent", "REDLINE", "speed_tier", 5, 45, 15),
    Challenge("serpent_shard", "signal_serpent", "SHARD HUNTER", "shards", 1),
    Challenge("blackglass_first", "blackglass", "FIRST VICTORY", "won", 1),
    Challenge("blackglass_normal", "blackglass", "CLEAR SIGNAL", "normal_win", 1, 45, 20),
    Challenge("blackglass_king_safe", "blackglass", "CROWN GUARD", "king_safe_win", 1, 50, 20),
    Challenge("blackglass_capture_5", "blackglass", "FIVE TAKEN", "captures", 5),
)


def level_for_xp(xp: int) -> int:
    return 1 + max(0, int(xp)) // 100


def progress_for_xp(xp: int) -> float:
    return (max(0, int(xp)) % 100) / 100


def ensure_mastery(profile) -> None:
    for game_id in GAME_TITLES:
        entry = profile.mastery.setdefault(game_id, {})
        entry.setdefault("xp", 0)
        entry.setdefault("games_played", 0)


def award_game_mastery(profile, game_id: str, score: int, won: bool = False) -> tuple[int, int]:
    ensure_mastery(profile)
    entry = profile.mastery[game_id]
    before = level_for_xp(entry["xp"])
    gained = 12 + min(28, max(0, int(score)) // 250) + (15 if won else 0)
    entry["xp"] += gained
    entry["games_played"] += 1
    return gained, level_for_xp(entry["xp"]) - before


def complete_challenges(profile, game_id: str, metrics: dict[str, int]) -> list[Challenge]:
    completed = []
    for challenge in CHALLENGES:
        if challenge.game_id != game_id or challenge.challenge_id in profile.completed_challenges:
            continue
        if int(metrics.get(challenge.metric, 0)) >= challenge.target:
            profile.completed_challenges.append(challenge.challenge_id)
            profile.mastery.setdefault(game_id, {"xp": 0, "games_played": 0})["xp"] += challenge.mastery_xp
            completed.append(challenge)
    return completed
