"""Rules tests for the first complete built-in game."""

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from games.void_merge import VoidMergeGame  # noqa: E402


class VoidMergeTests(unittest.TestCase):
    def setUp(self):
        self.game = VoidMergeGame(rng=random.Random(7))

    def test_new_game_starts_with_two_tiles(self):
        occupied = sum(value != 0 for row in self.game.board for value in row)
        self.assertEqual(occupied, 2)

    def test_merge_line_combines_each_tile_once(self):
        line, gain = self.game.merge_line([2, 2, 2, 2])
        self.assertEqual(line, [4, 4, 0, 0])
        self.assertEqual(gain, 8)
        line, gain = self.game.merge_line([4, 4, 8, 0])
        self.assertEqual(line, [8, 8, 0, 0])
        self.assertEqual(gain, 8)

    def test_move_changes_board_scores_and_spawns(self):
        self.game.board = [
            [2, 2, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        self.assertTrue(self.game.move("left"))
        self.assertEqual(self.game.score, 4)
        self.assertEqual(self.game.moves, 1)
        self.assertEqual(sum(value != 0 for row in self.game.board for value in row), 2)

    def test_locked_board_ends_game(self):
        self.game.board = [
            [2, 4, 2, 4],
            [4, 2, 4, 2],
            [2, 4, 2, 4],
            [4, 2, 4, 2],
        ]
        self.assertFalse(self.game.move("left"))
        self.assertTrue(self.game.game_over)

    def test_adjacent_match_keeps_game_alive(self):
        self.game.board = [
            [2, 2, 4, 8],
            [4, 8, 16, 32],
            [8, 16, 32, 64],
            [16, 32, 64, 128],
        ]
        self.assertTrue(self.game.has_moves())

    def test_target_sets_win_state_without_forcing_stop(self):
        self.game.board = [
            [1024, 1024, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        self.game.move("left")
        self.assertTrue(self.game.won)
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.highest_tile, 2048)

    def test_pause_blocks_moves(self):
        before = [row[:] for row in self.game.board]
        self.game.paused = True
        self.assertFalse(self.game.move("left"))
        self.assertEqual(self.game.board, before)


if __name__ == "__main__":
    unittest.main()
