"""Data-driven v0.3 achievement catalogue."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Achievement:
    achievement_id: str
    title: str
    category: str
    metric: str
    target: int
    flux: int = 15


ACHIEVEMENTS = (
    Achievement("first_bond", "FIRST BOND", "Companion", "care_actions", 1, 10),
    Achievement("loyal_friend", "LOYAL FRIEND", "Companion", "bond", 50, 35),
    Achievement("inseparable", "INSEPARABLE", "Companion", "bond", 100, 60),
    Achievement("nyx_level_5", "GROWING SIGNAL", "Companion", "level", 5, 30),
    Achievement("first_signal", "FIRST SIGNAL", "Games", "games_played", 1, 10),
    Achievement("arcade_regular", "ARCADE REGULAR", "Games", "games_played", 15, 35),
    Achievement("threefold", "THREEFOLD", "Games", "games_discovered", 3, 25),
    Achievement("merge_core", "MERGE CORE", "Games", "merge_tile", 512, 25),
    Achievement("serpent_line", "SERPENT LINE", "Games", "serpent_length", 20, 25),
    Achievement("blackglass_win", "BLACKGLASS VICTOR", "Games", "blackglass_wins", 1, 25),
    Achievement("first_craft", "MAKER", "Crafting", "crafted", 1, 15),
    Achievement("artificer", "ARTIFICER", "Crafting", "advanced_relics", 1, 35),
    Achievement("relic_keeper", "RELIC KEEPER", "Crafting", "relics_owned", 3, 20),
    Achievement("collector", "RELIC COLLECTOR", "Crafting", "relics_owned", 6, 55),
    Achievement("first_purchase", "FIRST TRADE", "Economy", "purchases", 1, 0),
    Achievement("market_regular", "MARKET REGULAR", "Economy", "purchases", 10, 35),
    Achievement("flux_saver", "FLUX RESERVE", "Economy", "flux", 500, 30),
    Achievement("field_walker", "FIELD WALKER", "Exploration", "explores", 10, 25),
    Achievement("void_walker", "VOID WALKER", "Exploration", "explores", 25, 50),
    Achievement("codex_reader", "CODEX READER", "Exploration", "discoveries", 10, 25),
    Achievement("signal_student", "SIGNAL STUDENT", "Mastery", "highest_mastery", 3, 30),
    Achievement("signal_master", "SIGNAL MASTER", "Mastery", "highest_mastery", 5, 60),
)


def newly_completed(completed: list[str], metrics: dict[str, int]) -> list[Achievement]:
    return [entry for entry in ACHIEVEMENTS if entry.achievement_id not in completed and metrics.get(entry.metric, 0) >= entry.target]
