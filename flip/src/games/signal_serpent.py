"""Grid rules for Signal Serpent, the second built-in Void Flip game."""

from __future__ import annotations

import random
import uuid


DIRECTIONS = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}


class SignalSerpentGame:
    width = 18
    height = 12

    def __init__(self, *, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        self.new_game()

    def new_game(self) -> None:
        center = (self.width // 2, self.height // 2)
        self.snake = [center, (center[0] - 1, center[1]), (center[0] - 2, center[1])]
        self.direction = DIRECTIONS["right"]
        self.queued_direction = self.direction
        self.signal = self._random_empty_cell()
        self.shard = None
        self.corruption: set[tuple[int, int]] = set()
        self.score = 0
        self.combo = 1
        self.best_combo = 1
        self.shards_collected = 0
        self.pickups = 0
        self.time_since_pickup = 99.0
        self.accumulator = 0.0
        self.paused = False
        self.game_over = False
        self.reward_applied = False
        self.run_id = uuid.uuid4().hex

    @property
    def length(self) -> int:
        return len(self.snake)

    @property
    def speed_tier(self) -> int:
        return min(8, 1 + max(0, self.length - 3) // 4)

    @property
    def step_interval(self) -> float:
        return max(0.08, 0.24 - (self.speed_tier - 1) * 0.022)

    def set_direction(self, name: str) -> bool:
        proposed = DIRECTIONS.get(name)
        if not proposed or self.game_over:
            return False
        if proposed[0] == -self.direction[0] and proposed[1] == -self.direction[1]:
            return False
        self.queued_direction = proposed
        return True

    def update(self, dt: float) -> int:
        if self.paused or self.game_over:
            return 0
        self.time_since_pickup += max(0.0, dt)
        self.accumulator += max(0.0, dt)
        steps = 0
        while self.accumulator >= self.step_interval and not self.game_over:
            self.accumulator -= self.step_interval
            self.step()
            steps += 1
        return steps

    def step(self) -> str:
        if self.paused or self.game_over:
            return "idle"
        self.direction = self.queued_direction
        head_x, head_y = self.snake[0]
        next_head = (head_x + self.direction[0], head_y + self.direction[1])
        body_collision = next_head in self.snake[:-1]
        wall_collision = not (0 <= next_head[0] < self.width and 0 <= next_head[1] < self.height)
        if wall_collision or body_collision or next_head in self.corruption:
            self.game_over = True
            return "game_over"

        self.snake.insert(0, next_head)
        if next_head == self.signal:
            self.combo = min(5, self.combo + 1) if self.time_since_pickup <= 4.0 else 1
            self.best_combo = max(self.best_combo, self.combo)
            self.score += 10 * self.combo
            self.pickups += 1
            self.time_since_pickup = 0.0
            self.signal = self._random_empty_cell()
            if self.shard is None and self.rng.random() < 0.12:
                self.shard = self._random_empty_cell()
            if self.pickups >= 6 and self.pickups % 4 == 0 and len(self.corruption) < 3:
                danger = self._random_empty_cell()
                if danger:
                    self.corruption.add(danger)
            return "signal"
        if self.shard is not None and next_head == self.shard:
            self.score += 25
            self.shards_collected += 1
            self.shard = None
            return "shard"
        self.snake.pop()
        return "move"

    def _random_empty_cell(self):
        blocked = set(getattr(self, "snake", [])) | set(getattr(self, "corruption", set()))
        signal = getattr(self, "signal", None)
        shard = getattr(self, "shard", None)
        if signal is not None:
            blocked.add(signal)
        if shard is not None:
            blocked.add(shard)
        available = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in blocked
        ]
        return self.rng.choice(available) if available else None
