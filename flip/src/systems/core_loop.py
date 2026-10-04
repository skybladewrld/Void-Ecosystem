"""Trusted coordinator connecting games, quests, economy, and the Voidling."""

from __future__ import annotations

import random
import uuid
from datetime import date

from content import ITEMS, RELICS
from systems.economy import buy
from systems.notifications import NotificationCenter
from systems.profile import CoreProfile
from systems.progression import UNLOCK_TITLES, newly_unlocked
from systems.quests import advance, ensure_daily
from systems.rewards import GameResult, RewardBundle, game_reward


class CoreLoop:
    def __init__(self, profile: CoreProfile, voidling, notifications: NotificationCenter):
        self.profile = profile
        self.voidling = voidling
        self.notifications = notifications
        if ensure_daily(profile):
            profile.add_activity("quests", "Daily objectives refreshed")
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

        summary = reward.summary()
        self.profile.add_activity("reward", f"{source} — {summary}")
        self.notifications.push("REWARD RECEIVED", summary)
        if gained_xp and track_xp_quest:
            self.record_event("xp_gained", gained_xp)
        self.track_voidling_milestones(old_level, old_bond)
        return True

    def track_voidling_milestones(self, old_level: int, old_bond: int) -> None:
        if self.voidling.level > old_level:
            self.profile.add_activity("level", f"Nyx reached Level {self.voidling.level}")
            self.notifications.push("LEVEL UP", f"NYX // LEVEL {self.voidling.level}")
            self.check_unlocks()
        if old_bond // 25 < self.voidling.bond // 25:
            milestone = (self.voidling.bond // 25) * 25
            self.profile.add_activity("bond", f"Nyx reached Bond {milestone}")
            self.notifications.push("BOND MILESTONE", f"NYX // BOND {milestone}")
        self.check_achievements()

    def check_achievements(self) -> None:
        achievements = (
            ("first_bond", self.voidling.total_actions >= 1, "FIRST BOND", 10),
            ("field_walker", self.voidling.total_actions >= 10, "FIELD WALKER", 25),
            ("relic_keeper", len(self.voidling.owned_relics) >= 3, "RELIC KEEPER", 20),
            ("true_companion", self.voidling.bond >= 50, "TRUE COMPANION", 50),
        )
        for achievement_id, earned, title, flux in achievements:
            reward_id = f"achievement:{achievement_id}"
            if earned and reward_id not in self.profile.claimed_rewards:
                self.notifications.push("ACHIEVEMENT", title)
                self.profile.add_activity("achievement", f"Achievement complete — {title}")
                self.apply_reward(reward_id, RewardBundle(flux=flux), f"ACHIEVEMENT {title}", track_xp_quest=False)

    def record_event(self, event_type: str, amount: int = 1) -> None:
        for quest, reward in advance(self.profile, event_type, amount):
            self.profile.add_activity("quest", f"Quest complete — {quest['title']}")
            self.notifications.push("QUEST COMPLETE", quest["title"])
            self.apply_reward(
                f"quest:{self.profile.quest_date}:{quest['id']}",
                reward,
                f"QUEST {quest['title']}",
                track_xp_quest=event_type != "xp_gained",
            )

    def finalize_game(self, result: GameResult) -> bool:
        reward = game_reward(result, self.current_relic())
        if not self.apply_reward(result.reward_id, reward, result.game_id.replace("_", " ").upper()):
            return False

        score = max(0, result.score)
        self.profile.add_activity("game", f"{result.game_id.replace('_', ' ').title()} — score {score:,}")
        self.record_event("game_played", 1)
        self.record_event("game_score", score)
        if result.game_id == "void_merge":
            highest = int(result.metrics.get("highest_tile", 0))
            self.record_event("merge_tile", highest)
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
        self.notifications.push("VOID MARKET", result.message)
        return result

    def check_unlocks(self) -> None:
        for module_id in newly_unlocked(self.voidling.level, self.profile.seen_unlocks):
            self.profile.seen_unlocks.append(module_id)
            title = UNLOCK_TITLES[module_id]
            self.profile.add_activity("unlock", f"Unlocked {title}")
            self.notifications.push("MODULE UNLOCKED", title)

    def refresh_quests(self, today: date | None = None) -> bool:
        return ensure_daily(self.profile, today)
