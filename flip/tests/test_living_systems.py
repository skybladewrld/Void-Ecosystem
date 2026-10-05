"""v0.3 mastery, quests, Codex, notifications, hardware, and input tests."""

import os
import sys
import unittest
from datetime import date
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hardware import MockHardwareAdapter  # noqa: E402
from input import Action, keyboard_action  # noqa: E402
from persistence import migrate_payload  # noqa: E402
from systems.achievements import newly_completed  # noqa: E402
from systems.codex import completion, discover  # noqa: E402
from systems.mastery import award_game_mastery, complete_challenges, level_for_xp  # noqa: E402
from systems.notifications import NotificationCenter  # noqa: E402
from systems.profile import CoreProfile  # noqa: E402
from systems.weekly import ensure_weekly, update_streak, week_key  # noqa: E402


class LivingSystemTests(unittest.TestCase):
    def test_mastery_thresholds_and_award(self):
        profile = CoreProfile()
        gained, levels = award_game_mastery(profile, "void_merge", 5000, True)
        self.assertGreater(gained, 0)
        self.assertEqual(level_for_xp(99), 1)
        self.assertEqual(level_for_xp(100), 2)
        self.assertGreaterEqual(levels, 0)

    def test_challenge_completes_exactly_once(self):
        profile = CoreProfile(mastery={"signal_serpent": {"xp": 0, "games_played": 0}})
        first = complete_challenges(profile, "signal_serpent", {"length": 20, "best_combo": 1})
        second = complete_challenges(profile, "signal_serpent", {"length": 30})
        self.assertEqual([entry.challenge_id for entry in first], ["serpent_length_20"])
        self.assertEqual(second, [])

    def test_weekly_generation_stable_and_refreshes(self):
        profile = CoreProfile()
        self.assertTrue(ensure_weekly(profile, date(2026, 10, 5)))
        first = [quest["id"] for quest in profile.weekly_quests]
        self.assertFalse(ensure_weekly(profile, date(2026, 10, 6)))
        self.assertEqual(first, [quest["id"] for quest in profile.weekly_quests])
        self.assertTrue(ensure_weekly(profile, date(2026, 10, 12)))
        self.assertEqual(profile.weekly_key, week_key(date(2026, 10, 12)))

    def test_streak_increments_or_resets_without_penalty(self):
        profile = CoreProfile(flux=300)
        update_streak(profile, date(2026, 10, 1))
        update_streak(profile, date(2026, 10, 2))
        self.assertEqual(profile.current_streak, 2)
        update_streak(profile, date(2026, 10, 5))
        self.assertEqual(profile.current_streak, 1)
        self.assertEqual(profile.flux, 300)

    def test_codex_discovery_is_idempotent(self):
        profile = CoreProfile()
        self.assertTrue(discover(profile, "games", "blackglass"))
        self.assertFalse(discover(profile, "games", "blackglass"))
        self.assertEqual(completion(profile, {"games": 3}), 1 / 3)

    def test_achievement_evaluation(self):
        entries = newly_completed([], {"games_played": 1})
        self.assertIn("first_signal", [entry.achievement_id for entry in entries])
        self.assertNotIn("arcade_regular", [entry.achievement_id for entry in entries])

    def test_v2_migrates_to_v3_without_losing_core_state(self):
        migrated = migrate_payload({"version": 2, "core": {"flux": 444, "quests": [{"id": "x"}]}, "voidling": {"name": "Nyx"}})
        self.assertEqual(migrated["version"], 3)
        self.assertEqual(migrated["core"]["flux"], 444)
        self.assertEqual(migrated["voidling"]["name"], "Nyx")
        self.assertIn("mastery", migrated["core"])

    def test_notification_queue_and_history_are_bounded(self):
        center = NotificationCenter()
        for index in range(40):
            center.push(f"N{index}", "message", "REWARD")
        self.assertLessEqual(len(center.queue), 30)
        self.assertEqual(len(center.history), 20)
        self.assertEqual(center.history[-1]["priority"], "REWARD")

    def test_mock_hardware_contract(self):
        adapter = MockHardwareAdapter(55, True, audio_available=False)
        snapshot = adapter.snapshot()
        self.assertEqual(snapshot.battery_percent, 55)
        self.assertTrue(snapshot.charging)
        self.assertFalse(snapshot.audio_available)
        self.assertEqual(adapter.display_metadata()["top"], (860, 386))

    def test_named_keyboard_actions(self):
        import pygame
        self.assertEqual(keyboard_action(pygame.K_UP, pygame), Action.UP)
        self.assertEqual(keyboard_action(pygame.K_RETURN, pygame), Action.A)
        self.assertEqual(keyboard_action(pygame.K_x, pygame), Action.X)


if __name__ == "__main__":
    unittest.main()
