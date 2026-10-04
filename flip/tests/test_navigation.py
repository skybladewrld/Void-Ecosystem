"""State tests that do not require a visible window."""

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app import MENU_ITEMS, VoidFlipApp  # noqa: E402


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

    def test_splash_home_and_modules_render(self):
        self.app.draw_splash(0.5)
        self.app.draw_console(1.0)
        for item in MENU_ITEMS:
            self.app.page = item
            self.app.draw_console(1.0)


if __name__ == "__main__":
    unittest.main()
