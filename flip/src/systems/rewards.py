"""Central game reward calculation and relic modifier application."""

from __future__ import annotations

from dataclasses import dataclass, field

from models import RelicDefinition


@dataclass(frozen=True)
class RewardBundle:
    flux: int = 0
    xp: int = 0
    bond: int = 0
    items: dict[str, int] = field(default_factory=dict)

    def summary(self) -> str:
        parts = []
        if self.flux:
            parts.append(f"+{self.flux} FLUX")
        if self.xp:
            parts.append(f"+{self.xp} XP")
        if self.bond:
            parts.append(f"+{self.bond} BOND")
        parts.extend(f"{item_id.replace('_', ' ').upper()} x{amount}" for item_id, amount in self.items.items())
        return " // ".join(parts) or "NO REWARD"


@dataclass(frozen=True)
class GameResult:
    reward_id: str
    game_id: str
    score: int
    metrics: dict[str, int | str | bool] = field(default_factory=dict)


def game_reward(result: GameResult, relic: RelicDefinition | None = None) -> RewardBundle:
    """Calculate a bounded reward without mutating trusted profile state."""

    score = max(0, int(result.score))
    items: dict[str, int] = {}
    bond = 0
    if result.game_id == "void_merge":
        xp = 2 + min(73, score // 80)
        flux = 0 if score < 100 else 3 + min(60, score // 120)
        highest = max(0, int(result.metrics.get("highest_tile", 0)))
        if highest >= 512:
            items["void_shard"] = 1
        if highest >= 2048:
            items["prism_seed"] = 1
    elif result.game_id == "signal_serpent":
        xp = 6 + min(70, score // 12)
        flux = 4 + min(60, score // 10)
        shards = min(3, max(0, int(result.metrics.get("shards", 0))))
        if shards:
            items["void_shard"] = shards
        if score >= 600:
            items["prism_seed"] = 1
    elif result.game_id == "blackglass":
        won = bool(result.metrics.get("won", 0))
        difficulty = str(result.metrics.get("difficulty", "NORMAL"))
        captures = min(12, max(0, int(result.metrics.get("captures", 0))))
        difficulty_bonus = {"EASY": 0, "NORMAL": 8, "HARD": 16}.get(difficulty, 0)
        xp = 4 + captures * 2 + (18 + difficulty_bonus if won else 0)
        flux = captures + 12 + difficulty_bonus if won else 0
        bond = 1 if won else 0
        if won and difficulty == "HARD" and captures >= 6:
            items["void_shard"] = 1
    else:
        return RewardBundle()

    if relic:
        xp = round(xp * relic.xp_multiplier)
        bond += relic.bond_bonus
        if relic.explore_find_bonus >= 0.30 and score >= 250:
            items["void_shard"] = items.get("void_shard", 0) + 1
    return RewardBundle(flux=flux, xp=xp, bond=bond, items=items)


def reward_tier(game_id: str, score: int) -> str:
    thresholds = (500, 1500, 4000) if game_id == "void_merge" else (150, 350, 650) if game_id == "blackglass" else (100, 300, 700)
    if score >= thresholds[2]:
        return "VOID"
    if score >= thresholds[1]:
        return "RARE"
    if score >= thresholds[0]:
        return "BRIGHT"
    return "BASE"
