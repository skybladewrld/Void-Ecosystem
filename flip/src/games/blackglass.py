"""Pure Blackglass Checkers rules and a lightweight CPU opponent."""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass


EMPTY = "."


@dataclass(frozen=True)
class Move:
    start: tuple[int, int]
    path: tuple[tuple[int, int], ...]
    captures: tuple[tuple[int, int], ...] = ()

    @property
    def end(self) -> tuple[int, int]:
        return self.path[-1]


def initial_board() -> list[list[str]]:
    board = [[EMPTY for _ in range(8)] for _ in range(8)]
    for row in range(3):
        for col in range(8):
            if (row + col) % 2:
                board[row][col] = "b"
    for row in range(5, 8):
        for col in range(8):
            if (row + col) % 2:
                board[row][col] = "w"
    return board


def owner(piece: str) -> str | None:
    return "black" if piece.lower() == "b" else "white" if piece.lower() == "w" else None


def directions(piece: str) -> tuple[tuple[int, int], ...]:
    if piece.isupper():
        return ((-1, -1), (-1, 1), (1, -1), (1, 1))
    step = 1 if piece == "b" else -1
    return ((step, -1), (step, 1))


def _inside(row: int, col: int) -> bool:
    return 0 <= row < 8 and 0 <= col < 8


def _capture_sequences(board: list[list[str]], start: tuple[int, int]) -> list[Move]:
    piece = board[start[0]][start[1]]
    side = owner(piece)
    results: list[Move] = []

    def walk(state, position, path, captures, moving_piece):
        found = False
        row, col = position
        for dr, dc in directions(moving_piece):
            mid = (row + dr, col + dc)
            end = (row + dr * 2, col + dc * 2)
            if not _inside(*end) or not _inside(*mid):
                continue
            jumped = state[mid[0]][mid[1]]
            if owner(jumped) in (None, side) or state[end[0]][end[1]] != EMPTY:
                continue
            found = True
            next_state = [line[:] for line in state]
            next_state[row][col] = EMPTY
            next_state[mid[0]][mid[1]] = EMPTY
            promoted = moving_piece
            if moving_piece == "b" and end[0] == 7:
                promoted = "B"
            elif moving_piece == "w" and end[0] == 0:
                promoted = "W"
            next_state[end[0]][end[1]] = promoted
            if promoted != moving_piece:
                results.append(Move(start, path + (end,), captures + (mid,)))
            else:
                walk(next_state, end, path + (end,), captures + (mid,), promoted)
        if not found and captures:
            results.append(Move(start, path, captures))

    walk(board, start, (), (), piece)
    return results


def legal_moves(board: list[list[str]], side: str) -> list[Move]:
    captures: list[Move] = []
    steps: list[Move] = []
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if owner(piece) != side:
                continue
            captures.extend(_capture_sequences(board, (row, col)))
            for dr, dc in directions(piece):
                end = (row + dr, col + dc)
                if _inside(*end) and board[end[0]][end[1]] == EMPTY:
                    steps.append(Move((row, col), (end,)))
    return captures or steps


def apply_move(board: list[list[str]], move: Move) -> list[list[str]]:
    if move not in legal_moves(board, owner(board[move.start[0]][move.start[1]]) or ""):
        raise ValueError("Illegal Blackglass move")
    result = [line[:] for line in board]
    piece = result[move.start[0]][move.start[1]]
    result[move.start[0]][move.start[1]] = EMPTY
    for row, col in move.captures:
        result[row][col] = EMPTY
    end_row, end_col = move.end
    if piece == "b" and end_row == 7:
        piece = "B"
    elif piece == "w" and end_row == 0:
        piece = "W"
    result[end_row][end_col] = piece
    return result


def winner(board: list[list[str]], turn: str) -> str | None:
    black = any(owner(piece) == "black" for row in board for piece in row)
    white = any(owner(piece) == "white" for row in board for piece in row)
    if not black:
        return "white"
    if not white:
        return "black"
    if not legal_moves(board, turn):
        return "white" if turn == "black" else "black"
    return None


def choose_cpu_move(board: list[list[str]], side: str, difficulty: str = "NORMAL", rng=None) -> Move | None:
    moves = legal_moves(board, side)
    if not moves:
        return None
    rng = rng or random.Random()
    if difficulty == "EASY":
        return rng.choice(moves)

    def score(move: Move) -> float:
        piece = board[move.start[0]][move.start[1]]
        promotion = 4 if (piece == "b" and move.end[0] == 7) or (piece == "w" and move.end[0] == 0) else 0
        center = 1.5 if 2 <= move.end[0] <= 5 and 2 <= move.end[1] <= 5 else 0
        king = 2 if piece.isupper() else 0
        value = len(move.captures) * 8 + promotion + center + king
        if difficulty == "HARD":
            next_board = apply_move(board, move)
            opponent = "white" if side == "black" else "black"
            reply = max((len(candidate.captures) for candidate in legal_moves(next_board, opponent)), default=0)
            value -= reply * 6
        return value

    best = max(score(move) for move in moves)
    return rng.choice([move for move in moves if score(move) == best])


class BlackglassGame:
    def __init__(self, mode: str = "CPU", difficulty: str = "NORMAL"):
        self.mode = mode
        self.difficulty = difficulty
        self.new_game()

    def new_game(self) -> None:
        self.board = initial_board()
        self.turn = "black"
        self.cursor = (2, 1)
        self.selected: tuple[int, int] | None = None
        self.paused = False
        self.game_over = False
        self.winner: str | None = None
        self.captures = {"black": 0, "white": 0}
        self.kings_created = {"black": 0, "white": 0}
        self.kings_lost = {"black": 0, "white": 0}
        self.run_id = uuid.uuid4().hex
        self.reward_applied = False

    def moves_from(self, square: tuple[int, int]) -> list[Move]:
        return [move for move in legal_moves(self.board, self.turn) if move.start == square]

    def play(self, move: Move) -> bool:
        if self.paused or self.game_over or move not in legal_moves(self.board, self.turn):
            return False
        old_piece = self.board[move.start[0]][move.start[1]]
        opponent = "white" if self.turn == "black" else "black"
        self.kings_lost[opponent] += sum(self.board[row][col].isupper() for row, col in move.captures)
        self.board = apply_move(self.board, move)
        self.captures[self.turn] += len(move.captures)
        if not old_piece.isupper() and self.board[move.end[0]][move.end[1]].isupper():
            self.kings_created[self.turn] += 1
        self.turn = "white" if self.turn == "black" else "black"
        self.winner = winner(self.board, self.turn)
        self.game_over = self.winner is not None
        self.selected = None
        return True

    def cpu_turn(self, rng=None) -> bool:
        if self.mode != "CPU" or self.turn != "white" or self.game_over or self.paused:
            return False
        move = choose_cpu_move(self.board, "white", self.difficulty, rng)
        if move is None:
            self.winner, self.game_over = "black", True
            return False
        return self.play(move)
