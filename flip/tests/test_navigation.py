"""State tests that do not require a visible window."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app import BOTTOM_BODY, MENU_ITEMS, TOP_BODY, VOIDLING_SECTIONS, VoidFlipApp  # noqa: E402
from content import ITEMS, RELICS, RELIC_RECIPES  # noqa: E402
from models import Voidling  # noqa: E402
from persistence import ProfileStore  # noqa: E402


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.app = VoidFlipApp(show_splash=False, persist=False)

    def tearDown(self):
        import pygame
        pygame.quit()

    def test_every_module_opens_and_returns_home(self):
        for index, item in enumerate(MENU_ITEMS):
            self.app.selected_index = index
            self.app.handle_action("select")
            self.assertEqual(self.app.page, item)
            self.app.handle_action("back")
            self.assertEqual(self.app.page, "HOME")

    def test_navigation_wraps(self):
        self.app.handle_action("up")
        self.assertEqual(self.app.selected_index, 6)
        self.app.handle_action("down")
        self.assertEqual(self.app.selected_index, 0)
        self.app.handle_action("left")
        self.assertEqual(self.app.selected_index, len(MENU_ITEMS) - 1)
        self.app.handle_action("right")
        self.assertEqual(self.app.selected_index, 0)

    def test_voidling_progress_is_bounded(self):
        self.assertTrue(self.app.voidling.name)
        self.assertGreaterEqual(self.app.voidling.xp_progress, 0)
        self.assertLessEqual(self.app.voidling.xp_progress, 1)

    def test_chassis_halves_are_equal_width(self):
        self.assertEqual(TOP_BODY.left, BOTTOM_BODY.left)
        self.assertEqual(TOP_BODY.width, BOTTOM_BODY.width)

    def test_first_complete_game_launches_and_returns_to_library(self):
        self.app.open_page("GAMES")
        self.app.handle_action("select")
        self.assertEqual(self.app.page, "VOID MERGE 2048")
        self.app.handle_action("back")
        self.assertEqual(self.app.page, "GAMES")

    def test_signal_serpent_launches_at_current_level(self):
        self.app.open_page("GAMES")
        self.app.module_index = 1
        self.app.handle_action("select")
        self.assertEqual(self.app.page, "SIGNAL SERPENT")

    def test_blackglass_launches_as_third_playable_game(self):
        self.app.open_page("GAMES")
        self.app.module_index = 2
        self.app.handle_action("select")
        self.assertEqual(self.app.page, "BLACKGLASS CHECKERS")
        self.app.draw_console(1.0)

    def test_scaled_window_preserves_logical_canvas(self):
        app = VoidFlipApp(show_splash=False, persist=False, window_scale=0.5)
        self.assertEqual(app.surface.get_size(), (1200, 900))
        self.assertEqual(app.window.get_size(), (600, 450))

    def test_market_purchase_updates_flux_and_inventory(self):
        self.app.open_page("MARKET")
        before_flux = self.app.core_profile.flux
        before_items = self.app.voidling.inventory.get("spark_fruit", 0)
        self.app.handle_action("select")
        self.assertEqual(self.app.core_profile.flux, before_flux - 25)
        self.assertEqual(self.app.voidling.inventory["spark_fruit"], before_items + 1)

    def test_voidling_sections_have_parent_navigation(self):
        self.app.open_page("VOIDLING")
        for index, section in enumerate(VOIDLING_SECTIONS):
            self.app.module_index = index
            self.app.handle_action("select")
            self.assertEqual(self.app.page, section)
            self.app.handle_action("back")
            self.assertEqual(self.app.page, "VOIDLING")

    def test_care_action_changes_real_state_and_has_cooldown(self):
        before = self.app.voidling.joy
        self.app.open_page("CARE")
        self.app.handle_action("select")
        self.assertGreater(self.app.voidling.joy, before)
        actions = self.app.voidling.total_actions
        self.app.handle_action("select")
        self.assertEqual(self.app.voidling.total_actions, actions)

    def test_item_use_consumes_inventory_and_changes_needs(self):
        self.app.voidling.fullness = 20
        before_quantity = self.app.voidling.inventory["spark_fruit"]
        result = self.app.voidling.use_item(ITEMS["spark_fruit"], self.app.current_relic())
        self.assertTrue(result.success)
        self.assertEqual(self.app.voidling.inventory["spark_fruit"], before_quantity - 1)
        self.assertGreater(self.app.voidling.fullness, 20)

    def test_relic_modifiers_and_crafting_are_functional(self):
        companion = Voidling(owned_relics=[], equipped_relic=None, inventory={"void_shard": 3, "moon_biscuit": 1})
        recipe = RELIC_RECIPES[0]
        result = companion.craft_relic(recipe, RELICS[recipe.relic_id])
        self.assertTrue(result.success)
        self.assertIn(recipe.relic_id, companion.owned_relics)
        self.assertNotIn("void_shard", companion.inventory)

    def test_battery_drains_and_charges(self):
        before = self.app.hardware.snapshot().battery_percent
        self.app.hardware.update(80)
        drained = self.app.hardware.snapshot().battery_percent
        self.assertLess(drained, before)
        self.app.hardware.set_charging(True)
        self.app.hardware.update(12)
        self.assertGreater(self.app.hardware.snapshot().battery_percent, drained)

    def test_starting_battery_can_be_overridden_for_device_testing(self):
        app = VoidFlipApp(show_splash=False, persist=False, battery_percent=0.1)
        self.assertAlmostEqual(app.hardware.snapshot().battery_percent, 0.1)

    def test_normal_simulator_launch_starts_fully_charged(self):
        app = VoidFlipApp(show_splash=False, persist=False)
        self.assertEqual(app.hardware.snapshot().battery_percent, 100.0)

    def test_old_saved_battery_does_not_override_full_charge_assumption(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            ProfileStore(path).save({"battery_percent": 0.1})
            app = VoidFlipApp(show_splash=False, save_path=path)
            self.assertEqual(app.hardware.snapshot().battery_percent, 100.0)

    def test_profile_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            store = ProfileStore(path)
            self.assertTrue(store.save({"voidling": self.app.voidling.to_dict(), "settings": self.app.settings, "battery_percent": 41.5}))
            loaded = store.load()
            self.assertEqual(loaded["voidling"]["name"], self.app.voidling.name)
            self.assertEqual(loaded["battery_percent"], 41.5)

    def test_settings_are_interactive(self):
        self.app.open_page("SETTINGS")
        original = self.app.settings["SCANLINES"]
        self.app.handle_action("select")
        self.assertNotEqual(self.app.settings["SCANLINES"], original)

    def test_splash_home_and_modules_render(self):
        self.app.draw_splash(0.5)
        self.app.draw_console(1.0)
        for item in (*MENU_ITEMS, *VOIDLING_SECTIONS):
            self.app.open_page(item)
            self.app.draw_console(1.0)
        self.app.open_page("VOID MERGE 2048")
        self.app.draw_console(1.0)
        self.app.open_page("SIGNAL SERPENT")
        self.app.draw_console(1.0)


if __name__ == "__main__":
    unittest.main()
