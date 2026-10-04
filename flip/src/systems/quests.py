"""Deterministic date-based daily quests."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date

from systems.rewards import RewardBundle


@dataclass(frozen=True)
class QuestDefinition:
    quest_id: str
    title: str
    description: str
    event_type: str
    target: int
    mode: str
    reward: RewardBundle


QUEST_POOL = (
    QuestDefinition("play_once", "SYSTEM CHECK", "Finish one built-in game run", "game_played", 1, "sum", RewardBundle(flux=12, xp=8)),
    QuestDefinition("merge_128", "MERGE MASTER", "Reach a 128 tile in Void Merge", "merge_tile", 128, "max", RewardBundle(flux=25, xp=50)),
    QuestDefinition("score_500", "SCORE PULSE", "Reach 500 points in one game", "game_score", 500, "max", RewardBundle(flux=20, xp=20)),
    QuestDefinition("care_three", "CARETAKER", "Perform 3 care actions", "care_action", 3, "sum", RewardBundle(flux=20, items={"spark_fruit": 1})),
    QuestDefinition("explore_twice", "EXPLORER", "Explore twice", "explore", 2, "sum", RewardBundle(flux=15, items={"void_shard": 1})),
    QuestDefinition("craft_once", "RELIC HAND", "Craft one relic", "craft", 1, "sum", RewardBundle(flux=30, xp=25)),
    QuestDefinition("use_two", "PACK LIGHT", "Use 2 inventory items", "item_used", 2, "sum", RewardBundle(flux=15, items={"moon_biscuit": 1})),
    QuestDefinition("gain_100_xp", "GROWTH SIGNAL", "Gain 100 XP", "xp_gained", 100, "sum", RewardBundle(flux=25)),
)

QUESTS_BY_ID = {quest.quest_id: quest for quest in QUEST_POOL}


def _new_quest(definition: QuestDefinition) -> dict:
    return {
        "id": definition.quest_id,
        "title": definition.title,
        "description": definition.description,
        "type": definition.event_type,
        "target": definition.target,
        "progress": 0,
        "completed": False,
        "claimed": False,
    }


def ensure_daily(profile, today: date | None = None) -> bool:
    today = today or date.today()
    key = today.isoformat()
    valid = len(profile.quests) == 3 and all(quest.get("id") in QUESTS_BY_ID for quest in profile.quests)
    if profile.quest_date == key and valid:
        return False
    rng = random.Random(today.toordinal())
    profile.quests = [_new_quest(quest) for quest in rng.sample(list(QUEST_POOL), 3)]
    profile.quest_date = key
    return True


def advance(profile, event_type: str, amount: int = 1) -> list[tuple[dict, RewardBundle]]:
    completed = []
    amount = max(0, int(amount))
    for quest in profile.quests:
        if quest.get("type") != event_type or quest.get("claimed"):
            continue
        definition = QUESTS_BY_ID.get(quest.get("id"))
        if not definition:
            continue
        if definition.mode == "max":
            quest["progress"] = max(int(quest.get("progress", 0)), amount)
        else:
            quest["progress"] = min(definition.target, int(quest.get("progress", 0)) + amount)
        if quest["progress"] >= definition.target:
            quest["completed"] = True
            quest["claimed"] = True
            completed.append((quest, definition.reward))
    return completed
