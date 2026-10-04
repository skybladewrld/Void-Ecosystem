"""Deterministic Signal Serpent rule tests."""

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from games.signal_serpent import SignalSerpentGame  # noqa: E402


class SignalSerpentTests(unittest.TestCase):
    def setUp(self):
        self.game = SignalSerpentGame(rng=random.Random(5))

    def test_moves_one_grid_cell(self):
        before = self.game.snake[0]
        self.game.step()
        self.assertEqual(self.game.snake[0], (before[0] + 1, before[1]))

    def test_cannot_reverse_directly_into_body(self):
        self.assertFalse(self.game.set_direction("left"))
        self.assertEqual(self.game.queued_direction, (1, 0))

    def test_signal_pickup_grows_scores_and_builds_combo(self):
        head = self.game.snake[0]
        self.game.signal = (head[0] + 1, head[1])
        self.game.time_since_pickup = 1.0
        event = self.game.step()
        self.assertEqual(event, "signal")
        self.assertEqual(self.game.length, 4)
        self.assertEqual(self.game.combo, 2)
        self.assertEqual(self.game.score, 20)

    def test_wall_collision_ends_run(self):
        self.game.snake = [(self.game.width - 1, 2), (self.game.width - 2, 2), (self.game.width - 3, 2)]
        self.game.direction = (1, 0)
        self.game.queued_direction = (1, 0)
        self.assertEqual(self.game.step(), "game_over")
        self.assertTrue(self.game.game_over)

    def test_self_collision_ends_run(self):
        self.game.snake = [(3, 3), (3, 4), (2, 4), (2, 3), (2, 2)]
        self.game.direction = (-1, 0)
        self.game.queued_direction = (0, 1)
        self.assertEqual(self.game.step(), "game_over")

    def test_pause_blocks_update(self):
        before = list(self.game.snake)
        self.game.paused = True
        self.assertEqual(self.game.update(1.0), 0)
        self.assertEqual(self.game.snake, before)

    def test_speed_increases_with_length(self):
        base_interval = self.game.step_interval
        self.game.snake.extend([(0, index) for index in range(8)])
        self.assertGreater(self.game.speed_tier, 1)
        self.assertLess(self.game.step_interval, base_interval)


if __name__ == "__main__":
    unittest.main()
