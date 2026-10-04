"""Lightweight non-blocking notification queue."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Notification:
    title: str
    message: str
    remaining: float = 3.4
    duration: float = 3.4


class NotificationCenter:
    def __init__(self):
        self.queue: list[Notification] = []
        self.active: Notification | None = None

    def push(self, title: str, message: str) -> None:
        self.queue.append(Notification(title[:28], message[:80]))
        if self.active is None:
            self.active = self.queue.pop(0)

    def update(self, dt: float) -> None:
        if not self.active:
            if self.queue:
                self.active = self.queue.pop(0)
            return
        self.active.remaining -= dt
        if self.active.remaining <= 0:
            self.active = self.queue.pop(0) if self.queue else None

    @property
    def progress(self) -> float:
        if not self.active:
            return 0.0
        return max(0.0, min(1.0, self.active.remaining / self.active.duration))
