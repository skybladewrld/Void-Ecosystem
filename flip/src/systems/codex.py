"""Discovery-focused Void Codex helpers."""

CODEX_CATEGORIES = ("items", "materials", "relics", "games", "achievements", "mastery_badges")


def ensure_codex(profile) -> None:
    for category in CODEX_CATEGORIES:
        profile.codex.setdefault(category, [])


def discover(profile, category: str, entry_id: str) -> bool:
    ensure_codex(profile)
    if category not in CODEX_CATEGORIES or entry_id in profile.codex[category]:
        return False
    profile.codex[category].append(entry_id)
    return True


def completion(profile, totals: dict[str, int]) -> float:
    ensure_codex(profile)
    discovered = sum(min(len(profile.codex.get(category, [])), total) for category, total in totals.items())
    possible = sum(totals.values())
    return discovered / possible if possible else 0.0
