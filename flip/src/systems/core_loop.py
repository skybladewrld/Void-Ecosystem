"""Trusted coordinator connecting games, quests, economy, and the Voidling."""

from __future__ import annotations

import random
import uuid
from datetime import date

from content import ITEMS, RELICS
from systems.achievements import newly_completed
from systems.codex import discover, ensure_codex
from systems.economy import buy
from systems.mastery import award_game_mastery, complete_challenges, ensure_mastery, level_for_xp
from systems.notifications import NotificationCenter
from systems.profile import CoreProfile
from systems.progression import UNLOCK_TITLES, newly_unlocked
from systems.quests import advance, ensure_daily
from systems.rewards import GameResult, RewardBundle, game_reward
from systems.weekly import advance_weekly, ensure_weekly, update_streak


class CoreLoop:
    def __init__(self, profile: CoreProfile, voidling, notifications: NotificationCenter):
        self.profile = profile
        self.voidling = voidling
        self.notifications = notifications
        if ensure_daily(profile):
            profile.add_activity("quests", "Daily objectives refreshed")
        if ensure_weekly(profile):
            profile.add_activity("quests", "Weekly objectives refreshed")
        ensure_mastery(profile)
        ensure_codex(profile)
        for item_id in voidling.inventory:
            discover(profile, "materials" if item_id in ("void_shard", "prism_seed") else "items", item_id)
        for relic_id in voidling.owned_relics:
            discover(profile, "relics", relic_id)
        available = newly_unlocked(voidling.level, profile.seen_unlocks)
        if not profile.seen_unlocks:
            profile.seen_unlocks.extend(available)
        else:
            self.check_unlocks()
        self.check_achievements()

    def current_relic(self):
        return RELICS.get(self.voidling.equipped_relic)

    def apply_reward(
        self,
        reward_id: str,
        reward: RewardBundle,
        source: str,
        *,
        track_xp_quest: bool = True,
    ) -> bool:
        if not self.profile.remember_reward(reward_id):
            return False
        old_level = self.voidling.level
        old_bond = self.voidling.bond
        self.profile.flux += max(0, reward.flux)
        gained_xp = self.voidling.gain_xp(max(0, reward.xp))
        self.voidling.bond += max(0, reward.bond)
        for item_id, amount in reward.items.items():
            if item_id in ITEMS and amount > 0:
                self.voidling.inventory[item_id] = self.voidling.inventory.get(item_id, 0) + int(amount)
                discover(self.profile, "materials" if item_id in ("void_shard", "prism_seed") else "items", item_id)

        summary = reward.summary()
        self.profile.add_activity("reward", f"{source} — {summary}")
        self.notifications.push("REWARD RECEIVED", summary, "REWARD")
        if gained_xp and track_xp_quest:
            self.record_event("xp_gained", gained_xp)
        self.track_voidling_milestones(old_level, old_bond)
        return True

    def track_voidling_milestones(self, old_level: int, old_bond: int) -> None:
        if self.voidling.level > old_level:
            self.profile.add_activity("level", f"Nyx reached Level {self.voidling.level}")
            self.notifications.push("LEVEL UP", f"NYX // LEVEL {self.voidling.level}", "IMPORTANT")
            self.check_unlocks()
        if old_bond // 25 < self.voidling.bond // 25:
            milestone = (self.voidling.bond // 25) * 25
            self.profile.add_activity("bond", f"Nyx reached Bond {milestone}")
            self.notifications.push("BOND MILESTONE", f"NYX // BOND {milestone}", "IMPORTANT")
        self.check_achievements()

    def check_achievements(self) -> None:
        stats = self.profile.profile_stats
        mastery_levels = [level_for_xp(value.get("xp", 0)) for value in self.profile.mastery.values()] or [1]
        metrics = {
            "care_actions": stats.get("care_actions", self.voidling.total_actions),
            "bond": self.voidling.bond,
            "level": self.voidling.level,
            "games_played": sum(value.get("games_played", 0) for value in self.profile.mastery.values()),
            "games_discovered": len(self.profile.codex.get("games", [])),
            "merge_tile": stats.get("merge_tile", 0),
            "serpent_length": self.profile.game_stats.get("signal_serpent_highest_length", 3),
            "blackglass_wins": self.profile.game_stats.get("blackglass_wins", 0),
            "crafted": stats.get("crafted", 0),
            "advanced_relics": len([item for item in self.voidling.owned_relics if item in ("prism_compass", "null_crown")]),
            "relics_owned": len(self.voidling.owned_relics),
            "purchases": stats.get("purchases", 0),
            "flux": self.profile.flux,
            "explores": stats.get("explores", 0),
            "discoveries": sum(len(entries) for entries in self.profile.codex.values()),
            "highest_mastery": max(mastery_levels),
        }
        for achievement in newly_completed(self.profile.completed_achievements, metrics):
            self.profile.completed_achievements.append(achievement.achievement_id)
            discover(self.profile, "achievements", achievement.achievement_id)
            self.notifications.push("ACHIEVEMENT", achievement.title, "IMPORTANT")
            self.profile.add_activity("achievement", f"Achievement complete — {achievement.title}")
            self.apply_reward(f"achievement:{achievement.achievement_id}", RewardBundle(flux=achievement.flux),
                              f"ACHIEVEMENT {achievement.title}", track_xp_quest=False)

    def record_event(self, event_type: str, amount: int = 1) -> None:
        for quest, reward in advance(self.profile, event_type, amount):
            self.profile.add_activity("quest", f"Quest complete — {quest['title']}")
            self.notifications.push("QUEST COMPLETE", quest["title"], "IMPORTANT")
            self.apply_reward(
                f"quest:{self.profile.quest_date}:{quest['id']}",
                reward,
                f"QUEST {quest['title']}",
                track_xp_quest=event_type != "xp_gained",
            )
        for quest, reward in advance_weekly(self.profile, event_type, amount):
            self.profile.add_activity("quest", f"Weekly complete — {quest['title']}")
            self.notifications.push("WEEKLY COMPLETE", quest["title"], "IMPORTANT")
            self.apply_reward(f"weekly:{self.profile.weekly_key}:{quest['id']}", reward,
                              f"WEEKLY {quest['title']}", track_xp_quest=event_type != "xp_gained")
        if self.profile.quests and all(quest.get("claimed") for quest in self.profile.quests):
            update_streak(self.profile, date.today())

    def finalize_game(self, result: GameResult) -> bool:
        reward = game_reward(result, self.current_relic())
        if not self.apply_reward(result.reward_id, reward, result.game_id.replace("_", " ").upper()):
            return False

        score = max(0, result.score)
        self.profile.add_activity("game", f"{result.game_id.replace('_', ' ').title()} — score {score:,}")
        self.record_event("game_played", 1)
        self.record_event("game_score", score)
        won = bool(result.metrics.get("won", 0))
        mastery_xp, levels = award_game_mastery(self.profile, result.game_id, score, won)
        discover(self.profile, "games", result.game_id)
        if levels:
            self.record_event("mastery_level", levels)
            level = level_for_xp(self.profile.mastery[result.game_id]["xp"])
            discover(self.profile, "mastery_badges", f"{result.game_id}:{level}")
            self.notifications.push("MASTERY UP", f"{result.game_id.replace('_', ' ').upper()} // LEVEL {level}", "IMPORTANT")
        for challenge in complete_challenges(self.profile, result.game_id, {"score": score, **result.metrics}):
            self.notifications.push("CHALLENGE COMPLETE", challenge.title, "REWARD")
            self.apply_reward(f"challenge:{challenge.challenge_id}", RewardBundle(flux=challenge.flux),
                              challenge.title, track_xp_quest=False)
        if result.game_id == "void_merge":
            highest = int(result.metrics.get("highest_tile", 0))
            self.record_event("merge_tile", highest)
            self.profile.profile_stats["merge_tile"] = max(self.profile.profile_stats.get("merge_tile", 0), highest)
            self.profile.game_stats["void_merge_runs"] += 1
            previous_high = self.profile.game_stats["void_merge_high_score"]
            self.profile.game_stats["void_merge_high_score"] = max(
                previous_high, score
            )
            if score > previous_high:
                self.notifications.push("NEW HIGH SCORE", f"VOID MERGE // {score:,}")
        elif result.game_id == "signal_serpent":
            stats = self.profile.game_stats
            stats["signal_serpent_total_runs"] += 1
            previous_high = stats["signal_serpent_high_score"]
            stats["signal_serpent_high_score"] = max(previous_high, score)
            if score > previous_high:
                self.notifications.push("NEW HIGH SCORE", f"SIGNAL SERPENT // {score:,}")
            stats["signal_serpent_highest_length"] = max(
                stats["signal_serpent_highest_length"], int(result.metrics.get("length", 3))
            )
            stats["signal_serpent_best_combo"] = max(
                stats["signal_serpent_best_combo"], int(result.metrics.get("best_combo", 1))
            )
        elif result.game_id == "blackglass":
            stats = self.profile.game_stats
            stats["blackglass_wins" if won else "blackglass_losses"] += 1
            stats["blackglass_best_captures"] = max(stats["blackglass_best_captures"], int(result.metrics.get("captures", 0)))
        self.profile.add_activity("mastery", f"+{mastery_xp} mastery XP — {result.game_id.replace('_', ' ').title()}")
        self.check_achievements()
        return True

    def purchase(self, sku: str, *, rng: random.Random | None = None):
        result = buy(self.profile, sku, rng)
        if not result.success:
            self.notifications.push("PURCHASE FAILED", result.message)
            return result
        self.apply_reward(
            f"market:{uuid.uuid4().hex}",
            result.reward,
            result.message,
            track_xp_quest=False,
        )
        self.profile.add_activity("market", f"{result.message} — Flux {self.profile.flux}")
        self.profile.profile_stats["purchases"] += 1
        self.notifications.push("VOID MARKET", result.message)
        self.check_achievements()
        return result

    def check_unlocks(self) -> None:
        for module_id in newly_unlocked(self.voidling.level, self.profile.seen_unlocks):
            self.profile.seen_unlocks.append(module_id)
            title = UNLOCK_TITLES[module_id]
            self.profile.add_activity("unlock", f"Unlocked {title}")
            self.notifications.push("MODULE UNLOCKED", title, "IMPORTANT")

    def refresh_quests(self, today: date | None = None) -> bool:
        daily = ensure_daily(self.profile, today)
        weekly = ensure_weekly(self.profile, today)
        return daily or weekly
