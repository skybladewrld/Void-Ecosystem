"""Deterministic rules for Void Merge 2048."""

from __future__ import annotations

import random
import uuid


class VoidMergeGame:
    size = 4
    target = 2048

    def __init__(self, *, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        self.board: list[list[int]] = []
        self.score = 0
        self.moves = 0
        self.merges = 0
        self.won = False
        self.game_over = False
        self.paused = False
        self.last_gain = 0
        self.new_game()

    def new_game(self) -> None:
        self.board = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.score = 0
        self.moves = 0
        self.merges = 0
        self.won = False
        self.game_over = False
        self.paused = False
        self.last_gain = 0
        self.reward_applied = False
        self.run_id = uuid.uuid4().hex
        self.spawn_tile()
        self.spawn_tile()

    def empty_cells(self) -> list[tuple[int, int]]:
        return [
            (row, column)
            for row in range(self.size)
            for column in range(self.size)
            if self.board[row][column] == 0
        ]

    def spawn_tile(self) -> bool:
        empty = self.empty_cells()
        if not empty:
            return False
        row, column = self.rng.choice(empty)
        self.board[row][column] = 4 if self.rng.random() < 0.1 else 2
        return True

    @staticmethod
    def merge_line(line: list[int]) -> tuple[list[int], int]:
        compact = [value for value in line if value]
        merged: list[int] = []
        gain = 0
        index = 0
        while index < len(compact):
            if index + 1 < len(compact) and compact[index] == compact[index + 1]:
                value = compact[index] * 2
                merged.append(value)
                gain += value
                index += 2
            else:
                merged.append(compact[index])
                index += 1
        return merged + [0] * (len(line) - len(merged)), gain

    def move(self, direction: str) -> bool:
        if self.paused or self.game_over:
            return False
        before = [row[:] for row in self.board]
        total_gain = 0

        if direction in ("left", "right"):
            for row_index in range(self.size):
                source = self.board[row_index][:]
                if direction == "right":
                    source.reverse()
                result, gain = self.merge_line(source)
                if direction == "right":
                    result.reverse()
                self.board[row_index] = result
                total_gain += gain
        elif direction in ("up", "down"):
            for column in range(self.size):
                source = [self.board[row][column] for row in range(self.size)]
                if direction == "down":
                    source.reverse()
                result, gain = self.merge_line(source)
                if direction == "down":
                    result.reverse()
                for row in range(self.size):
                    self.board[row][column] = result[row]
                total_gain += gain
        else:
            return False

        if self.board == before:
            self.game_over = not self.has_moves()
            return False

        self.score += total_gain
        if total_gain:
            self.merges += 1
        self.last_gain = total_gain
        self.moves += 1
        self.won = self.won or any(value >= self.target for row in self.board for value in row)
        self.spawn_tile()
        self.game_over = not self.has_moves()
        return True

    def has_moves(self) -> bool:
        if self.empty_cells():
            return True
        for row in range(self.size):
            for column in range(self.size):
                value = self.board[row][column]
                if column + 1 < self.size and self.board[row][column + 1] == value:
                    return True
                if row + 1 < self.size and self.board[row + 1][column] == value:
                    return True
        return False

    @property
    def highest_tile(self) -> int:
        return max(max(row) for row in self.board)
