"""Calendar-week quests and forgiving daily completion streaks."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta

from systems.rewards import RewardBundle


@dataclass(frozen=True)
class WeeklyDefinition:
    quest_id: str
    title: str
    description: str
    event_type: str
    target: int
    reward: RewardBundle


WEEKLY_POOL = (
    WeeklyDefinition("weekly_games", "PLAYGROUND", "Finish 8 game sessions", "game_played", 8, RewardBundle(flux=80, xp=70)),
    WeeklyDefinition("weekly_care", "DEEP CARE", "Perform 15 care actions", "care_action", 15, RewardBundle(flux=65, xp=80)),
    WeeklyDefinition("weekly_craft", "ARTIFICER", "Craft 2 relics", "craft", 2, RewardBundle(flux=90, items={"prism_seed": 1})),
    WeeklyDefinition("weekly_mastery", "SIGNAL STUDY", "Gain 2 mastery levels", "mastery_level", 2, RewardBundle(flux=90, xp=60)),
    WeeklyDefinition("weekly_explore", "VOID WALK", "Explore 8 times", "explore", 8, RewardBundle(flux=70, items={"void_shard": 2})),
)

WEEKLY_BY_ID = {entry.quest_id: entry for entry in WEEKLY_POOL}


def week_key(today: date) -> str:
    year, week, _ = today.isocalendar()
    return f"{year}-W{week:02d}"


def ensure_weekly(profile, today: date | None = None) -> bool:
    today = today or date.today()
    key = week_key(today)
    valid = len(profile.weekly_quests) == 2 and all(q.get("id") in WEEKLY_BY_ID for q in profile.weekly_quests)
    if profile.weekly_key == key and valid:
        return False
    rng = random.Random(key)
    profile.weekly_quests = [{"id": q.quest_id, "title": q.title, "description": q.description, "type": q.event_type,
                              "target": q.target, "progress": 0, "completed": False, "claimed": False}
                             for q in rng.sample(list(WEEKLY_POOL), 2)]
    profile.weekly_key = key
    return True


def advance_weekly(profile, event_type: str, amount: int = 1):
    completed = []
    for quest in profile.weekly_quests:
        if quest.get("type") != event_type or quest.get("claimed"):
            continue
        definition = WEEKLY_BY_ID[quest["id"]]
        quest["progress"] = min(definition.target, int(quest.get("progress", 0)) + max(0, int(amount)))
        if quest["progress"] >= definition.target:
            quest["completed"] = quest["claimed"] = True
            completed.append((quest, definition.reward))
    return completed


def update_streak(profile, completion_day: date) -> bool:
    key = completion_day.isoformat()
    if profile.last_daily_completion == key:
        return False
    previous = date.fromisoformat(profile.last_daily_completion) if profile.last_daily_completion else None
    profile.current_streak = profile.current_streak + 1 if previous == completion_day - timedelta(days=1) else 1
    profile.longest_streak = max(profile.longest_streak, profile.current_streak)
    profile.last_daily_completion = key
    return True
