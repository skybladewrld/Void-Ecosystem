"""Level-derived module unlock rules."""

UNLOCK_LEVELS = {
    "voidling": 1,
    "void_merge": 1,
    "workshop": 2,
    "signal_serpent": 3,
    "market": 3,
    "advanced_relics": 5,
}

UNLOCK_TITLES = {
    "voidling": "VOIDLING CARE",
    "void_merge": "VOID MERGE",
    "workshop": "RELIC WORKSHOP",
    "signal_serpent": "SIGNAL SERPENT",
    "market": "VOID MARKET",
    "advanced_relics": "ADVANCED RELICS",
}


def is_unlocked(module_id: str, level: int) -> bool:
    return level >= UNLOCK_LEVELS.get(module_id, 1)


def newly_unlocked(level: int, seen: list[str]) -> list[str]:
    return [module_id for module_id, required in UNLOCK_LEVELS.items() if level >= required and module_id not in seen]
