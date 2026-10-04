"""State tests that do not require a visible window."""

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app import BOTTOM_BODY, MENU_ITEMS, TOP_BODY, VoidFlipApp  # noqa: E402


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.app = VoidFlipApp(show_splash=False)

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
        self.assertEqual(self.app.selected_index, len(MENU_ITEMS) - 1)
        self.app.handle_action("down")
        self.assertEqual(self.app.selected_index, 0)

    def test_voidling_progress_is_bounded(self):
        self.assertTrue(self.app.voidling.name)
        self.assertGreaterEqual(self.app.voidling.xp_progress, 0)
        self.assertLessEqual(self.app.voidling.xp_progress, 1)

    def test_chassis_halves_are_equal_width(self):
        self.assertEqual(TOP_BODY.left, BOTTOM_BODY.left)
        self.assertEqual(TOP_BODY.width, BOTTOM_BODY.width)

    def test_first_game_launches_and_back_returns_to_library(self):
        self.app.open_page("GAMES")
        self.app.handle_action("select")
        self.assertEqual(self.app.page, "SIGNAL CATCH")
        self.app.handle_action("right")
        self.assertGreater(self.app.game_player_x, 430)
        self.app.handle_action("back")
        self.assertEqual(self.app.page, "GAMES")

    def test_settings_are_interactive(self):
        self.app.open_page("SETTINGS")
        original = self.app.settings["SCANLINES"]
        self.app.handle_action("select")
        self.assertNotEqual(self.app.settings["SCANLINES"], original)

    def test_splash_home_and_modules_render(self):
        self.app.draw_splash(0.5)
        self.app.draw_console(1.0)
        for item in MENU_ITEMS:
            self.app.page = item
            self.app.draw_console(1.0)
        self.app.page = "SIGNAL CATCH"
        self.app.draw_console(1.0)


if __name__ == "__main__":
    unittest.main()
