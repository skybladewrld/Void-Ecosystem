"""Pure Core Loop system tests."""

import random
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from content import RELICS  # noqa: E402
from models import Voidling  # noqa: E402
from persistence import ProfileStore, SAVE_VERSION, migrate_payload  # noqa: E402
from systems.core_loop import CoreLoop  # noqa: E402
from systems.economy import MARKET_BY_SKU, MYSTERY_CACHE_LOOT, buy  # noqa: E402
from systems.notifications import NotificationCenter  # noqa: E402
from systems.profile import CoreProfile  # noqa: E402
from systems.progression import is_unlocked  # noqa: E402
from systems.quests import QUESTS_BY_ID, advance, ensure_daily  # noqa: E402
from systems.rewards import GameResult, RewardBundle, game_reward  # noqa: E402


class CoreSystemTests(unittest.TestCase):
    def test_daily_quests_are_stable_for_date_and_refresh_next_date(self):
        profile = CoreProfile()
        today = date(2026, 10, 4)
        self.assertTrue(ensure_daily(profile, today))
        first_ids = [quest["id"] for quest in profile.quests]
        self.assertFalse(ensure_daily(profile, today))
        self.assertEqual(first_ids, [quest["id"] for quest in profile.quests])
        self.assertTrue(ensure_daily(profile, today + timedelta(days=1)))
        self.assertEqual(profile.quest_date, "2026-10-05")

    def test_quest_progress_and_auto_claim_happen_once(self):
        definition = QUESTS_BY_ID["care_three"]
        profile = CoreProfile(quests=[{
            "id": definition.quest_id,
            "title": definition.title,
            "description": definition.description,
            "type": definition.event_type,
            "target": definition.target,
            "progress": 0,
            "completed": False,
            "claimed": False,
        }])
        self.assertEqual(advance(profile, "care_action", 2), [])
        completed = advance(profile, "care_action", 1)
        self.assertEqual(len(completed), 1)
        self.assertTrue(profile.quests[0]["claimed"])
        self.assertEqual(advance(profile, "care_action", 5), [])

    def test_market_spends_flux_and_rejects_insufficient_balance(self):
        profile = CoreProfile(flux=25)
        result = buy(profile, "spark_fruit")
        self.assertTrue(result.success)
        self.assertEqual(profile.flux, 0)
        self.assertEqual(result.reward.items, {"spark_fruit": 1})
        result = buy(profile, "repair_gel")
        self.assertFalse(result.success)
        self.assertEqual(profile.flux, 0)

    def test_mystery_cache_always_uses_controlled_loot(self):
        valid = [reward.items for reward in MYSTERY_CACHE_LOOT]
        for seed in range(30):
            profile = CoreProfile(flux=MARKET_BY_SKU["mystery_cache"].price)
            result = buy(profile, "mystery_cache", random.Random(seed))
            self.assertIn(result.reward.items, valid)

    def test_game_reward_applies_relic_modifier_in_one_place(self):
        result = GameResult("run-1", "void_merge", 800, {"highest_tile": 512})
        plain = game_reward(result)
        boosted = game_reward(result, RELICS["echo_lens"])
        self.assertGreater(boosted.xp, plain.xp)
        self.assertEqual(boosted.flux, plain.flux)
        self.assertEqual(plain.items, {"void_shard": 1})

    def test_duplicate_game_reward_is_not_applied_twice(self):
        profile = CoreProfile()
        companion = Voidling()
        core = CoreLoop(profile, companion, NotificationCenter())
        result = GameResult("same-run", "void_merge", 1000, {"highest_tile": 512})
        before_flux = profile.flux
        self.assertTrue(core.finalize_game(result))
        after_flux = profile.flux
        self.assertGreater(after_flux, before_flux)
        self.assertFalse(core.finalize_game(result))
        self.assertEqual(profile.flux, after_flux)

    def test_unlock_thresholds(self):
        self.assertTrue(is_unlocked("void_merge", 1))
        self.assertFalse(is_unlocked("signal_serpent", 2))
        self.assertTrue(is_unlocked("signal_serpent", 3))
        self.assertFalse(is_unlocked("advanced_relics", 4))

    def test_v1_save_migrates_without_losing_existing_fields(self):
        old = {"version": 1, "voidling": {"name": "Nyx"}, "settings": {"SCANLINES": False}}
        migrated = migrate_payload(old)
        self.assertEqual(migrated["version"], SAVE_VERSION)
        self.assertEqual(migrated["voidling"]["name"], "Nyx")
        self.assertEqual(migrated["core"]["flux"], 120)

    def test_profile_store_writes_backup_before_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            store = ProfileStore(path)
            self.assertTrue(store.save({"core": {"flux": 10}}))
            self.assertTrue(store.save({"core": {"flux": 20}}))
            self.assertTrue(path.with_suffix(".json.bak").exists())
            self.assertEqual(store.load()["core"]["flux"], 20)


if __name__ == "__main__":
    unittest.main()
