"""v0.3.1 navigation, layout, confirmation, and device-state tests."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app import VOIDLING_SECTIONS, VoidFlipApp  # noqa: E402
from content import RELIC_RECIPES  # noqa: E402
from games.blackglass import EMPTY, legal_moves  # noqa: E402
from ui.layout import board_to_visual, capture_required, recipe_availability, scroll_window, visual_delta_to_board  # noqa: E402


class PolishSystemTests(unittest.TestCase):
    def setUp(self):
        self.app = VoidFlipApp(show_splash=False, persist=False)

    def tearDown(self):
        import pygame
        pygame.quit()

    def test_scroll_window_keeps_every_selection_visible(self):
        for selected in range(12):
            start, end = scroll_window(selected, 12, 5)
            self.assertLessEqual(start, selected)
            self.assertGreater(end, selected)
            self.assertLessEqual(end - start, 5)

    def test_voidling_uses_five_reachable_tabs(self):
        self.assertEqual(VOIDLING_SECTIONS, ("STATUS", "CARE", "ITEMS", "RELICS", "JOURNAL"))
        self.app.open_page("VOIDLING")
        for expected in range(1, 5):
            self.app.handle_action("right")
            self.assertEqual(self.app.module_index, expected)

    def test_back_stack_restores_game_list_selection(self):
        self.app.open_page("GAMES")
        self.app.module_index = 2
        self.app.handle_action("select")
        self.assertEqual(self.app.page, "GAME DETAIL")
        self.app.handle_action("back")
        self.assertEqual(self.app.page, "GAMES")
        self.assertEqual(self.app.module_index, 2)

    def test_market_requires_second_confirmation_press(self):
        self.app.open_page("MARKET")
        balance = self.app.core_profile.flux
        self.app.handle_action("select")
        self.assertEqual(self.app.core_profile.flux, balance)
        self.assertEqual(self.app.market_confirmation, "spark_fruit")
        self.app.handle_action("select")
        self.assertEqual(self.app.core_profile.flux, balance - 25)
        self.assertIsNone(self.app.market_confirmation)

    def test_workshop_availability_explains_missing_and_owned(self):
        recipe = RELIC_RECIPES[0]
        self.assertEqual(recipe_availability(recipe, {}, [], False), (False, "MISSING MATERIALS"))
        self.assertEqual(recipe_availability(recipe, {}, [recipe.relic_id], False), (False, "OWNED"))
        inventory = dict(recipe.ingredients)
        self.assertEqual(recipe_availability(recipe, inventory, [], False), (True, "READY TO CRAFT"))

    def test_sleep_preserves_page_and_pauses_game(self):
        self.app.open_page("SIGNAL SERPENT")
        self.app.handle_action("home")
        self.assertTrue(self.app.sleeping)
        self.assertTrue(self.app.signal_serpent.paused)
        self.app.handle_action("home")
        self.assertFalse(self.app.sleeping)
        self.assertEqual(self.app.page, "SIGNAL SERPENT")

    def test_quick_settings_overlay_is_global_and_non_navigating(self):
        self.app.open_page("MARKET")
        self.app.handle_action("select_menu")
        self.assertTrue(self.app.quick_settings)
        self.assertEqual(self.app.page, "MARKET")
        self.app.handle_action("back")
        self.assertFalse(self.app.quick_settings)

    def test_display_preferences_round_trip_without_schema_change(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            app = VoidFlipApp(show_splash=False, save_path=path)
            app.brightness = 0.7
            app.audio.master = 0.4
            app.save_state()
            loaded = VoidFlipApp(show_splash=False, save_path=path)
            self.assertAlmostEqual(loaded.brightness, 0.7)
            self.assertAlmostEqual(loaded.audio.master, 0.4)

    def test_blackglass_human_side_maps_to_visual_bottom(self):
        self.assertEqual(board_to_visual((0, 1), True)[0], 7)
        self.assertEqual(board_to_visual((7, 0), True)[0], 0)
        self.assertEqual(visual_delta_to_board((-1, 0), True), (1, 0))

    def test_forced_capture_state_matches_legal_moves(self):
        board = [[EMPTY for _ in range(8)] for _ in range(8)]
        board[2][1], board[3][2], board[2][5] = "b", "w", "b"
        moves = legal_moves(board, "black")
        self.assertTrue(capture_required(moves))
        self.assertEqual({move.start for move in moves}, {(2, 1)})


if __name__ == "__main__":
    unittest.main()
