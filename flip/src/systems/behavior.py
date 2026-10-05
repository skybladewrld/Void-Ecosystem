"""Low-cost contextual behavior and thoughts for Nyx."""

from __future__ import annotations

import random
import time


THOUGHTS = {
    "HUNGRY": ("I'm getting hungry...", "A Spark Fruit would be nice."),
    "TIRED": ("Could we rest for a bit?", "My signal feels dim."),
    "WORRIED": ("It's quiet. Stay close?", "I hope everything is okay."),
    "SLEEPING": ("...soft signal static...", "Just one more minute."),
    "EXCITED": ("Something strange is nearby!", "Let's see what we found!"),
    "CELEBRATING": ("We did it!", "That was a brilliant signal!"),
    "PROUD": ("We're becoming quite a team.", "Look how far we've come."),
    "HAPPY": ("I like being here with you.", "The system feels bright today."),
    "CURIOUS": ("I wonder what we'll find today.", "Which signal should we follow?"),
    "IDLE": ("I'm watching the system pulse.", "Everything sounds calm."),
}


class NyxBehavior:
    def __init__(self, metadata: dict | None = None):
        data = metadata or {}
        self.reaction = str(data.get("reaction", ""))
        self.reaction_until = float(data.get("reaction_until", 0.0))
        self.thought = str(data.get("thought", "I wonder what we'll find today."))
        self.next_thought_at = 0.0

    def react(self, state: str, duration: float = 5.0, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        self.reaction = state.upper()
        self.reaction_until = now + duration
        self.next_thought_at = 0.0

    def state(self, voidling, now: float | None = None) -> str:
        now = time.monotonic() if now is None else now
        if self.reaction and now < self.reaction_until:
            return self.reaction
        if voidling.energy < 12:
            return "SLEEPING"
        if voidling.last_actions and time.time() - max(voidling.last_actions.values()) > 3600:
            return "WORRIED"
        if voidling.health < 35 or voidling.joy < 25:
            return "WORRIED"
        if voidling.fullness < 30:
            return "HUNGRY"
        if voidling.energy < 25:
            return "TIRED"
        if voidling.energy > 88 and voidling.fullness > 75 and voidling.joy > 75:
            return "HAPPY"
        if voidling.bond >= 50:
            return "PROUD"
        return "CURIOUS" if voidling.joy >= 45 else "IDLE"

    def current_thought(self, voidling, context="HOME", now: float | None = None, rng=None) -> str:
        now = time.monotonic() if now is None else now
        if now >= self.next_thought_at:
            state = self.state(voidling, now)
            contextual = {
                "GAMES": "Which one are we playing?",
                "MARKET": "Do we need supplies?",
                "WORKSHOP": "I like that relic.",
                "QUESTS": "We can finish these together.",
                "BLACKGLASS CHECKERS": "Think two moves ahead.",
            }.get(context)
            choices = THOUGHTS.get(state, THOUGHTS["IDLE"])
            self.thought = contextual or (rng or random).choice(choices)
            self.next_thought_at = now + 18.0
        return self.thought

    def to_dict(self) -> dict:
        return {"reaction": self.reaction, "reaction_until": 0.0, "thought": self.thought}
