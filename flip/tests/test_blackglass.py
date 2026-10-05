"""Pure Blackglass Checkers rules."""

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from games.blackglass import EMPTY, BlackglassGame, apply_move, choose_cpu_move, initial_board, legal_moves, winner  # noqa: E402


def blank():
    return [[EMPTY for _ in range(8)] for _ in range(8)]


class BlackglassTests(unittest.TestCase):
    def test_initial_board_has_twelve_pieces_per_side(self):
        board = initial_board()
        self.assertEqual(sum(piece.lower() == "b" for row in board for piece in row), 12)
        self.assertEqual(sum(piece.lower() == "w" for row in board for piece in row), 12)

    def test_standard_diagonal_moves(self):
        moves = legal_moves(initial_board(), "black")
        self.assertEqual(len(moves), 7)
        self.assertTrue(all(not move.captures for move in moves))

    def test_capture_is_forced(self):
        board = blank()
        board[2][1], board[3][2], board[2][5] = "b", "w", "b"
        moves = legal_moves(board, "black")
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves[0].captures, ((3, 2),))

    def test_multi_jump_is_one_complete_move(self):
        board = blank()
        board[1][0], board[2][1], board[4][3] = "b", "w", "w"
        move = legal_moves(board, "black")[0]
        self.assertEqual(move.path, ((3, 2), (5, 4)))
        self.assertEqual(len(move.captures), 2)

    def test_promotion_creates_king(self):
        board = blank()
        board[6][1] = "b"
        move = next(move for move in legal_moves(board, "black") if move.end == (7, 0))
        result = apply_move(board, move)
        self.assertEqual(result[7][0], "B")

    def test_king_moves_both_directions(self):
        board = blank()
        board[4][3] = "B"
        ends = {move.end for move in legal_moves(board, "black")}
        self.assertEqual(ends, {(3, 2), (3, 4), (5, 2), (5, 4)})

    def test_no_legal_move_loses(self):
        board = blank()
        board[7][0], board[0][1] = "b", "w"
        self.assertEqual(winner(board, "black"), "white")

    def test_cpu_always_returns_legal_move(self):
        board = initial_board()
        legal = legal_moves(board, "black")
        for difficulty in ("EASY", "NORMAL", "HARD"):
            self.assertIn(choose_cpu_move(board, "black", difficulty, random.Random(4)), legal)

    def test_game_tracks_captures_and_turn(self):
        game = BlackglassGame(mode="LOCAL")
        game.board = blank()
        game.board[2][1], game.board[3][2], game.board[6][1] = "b", "w", "w"
        self.assertTrue(game.play(legal_moves(game.board, "black")[0]))
        self.assertEqual(game.captures["black"], 1)
        self.assertEqual(game.turn, "white")


if __name__ == "__main__":
    unittest.main()
