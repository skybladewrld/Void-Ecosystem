"""Data models and rules for the Voidling progression system."""

from __future__ import annotations

import math
import random
import time
from dataclasses import asdict, dataclass, field


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


@dataclass(frozen=True)
class ItemDefinition:
    """A platform-owned item definition with real care effects."""

    item_id: str
    name: str
    category: str
    rarity: str
    description: str
    energy: int = 0
    fullness: int = 0
    joy: int = 0
    health: int = 0
    bond: int = 0
    usable: bool = True


@dataclass(frozen=True)
class RelicDefinition:
    """An equipable modifier. Every field is consumed by simulation rules."""

    relic_id: str
    name: str
    rarity: str
    slot: str
    description: str
    xp_multiplier: float = 1.0
    decay_multiplier: float = 1.0
    care_multiplier: float = 1.0
    explore_find_bonus: float = 0.0
    energy_cap_bonus: int = 0
    bond_bonus: int = 0


@dataclass(frozen=True)
class RelicRecipe:
    """A deterministic recipe owned by the platform, not by a game."""

    relic_id: str
    ingredients: dict[str, int]


@dataclass(frozen=True)
class GameEntry:
    """A game in the curated roadmap or installed library."""

    game_id: str
    title: str
    genre: str
    status: str
    description: str
    players: str = "1P"
    playable: bool = False


@dataclass(frozen=True)
class ActionResult:
    success: bool
    message: str
    xp_gained: int = 0
    reward_item_id: str | None = None


@dataclass
class Voidling:
    """Persistent companion state and the rules that are allowed to change it."""

    name: str = "Nyx"
    level: int = 3
    xp: int = 42
    energy: float = 78.0
    fullness: float = 72.0
    joy: float = 68.0
    health: float = 100.0
    bond: int = 12
    total_actions: int = 0
    inventory: dict[str, int] = field(
        default_factory=lambda: {
            "void_shard": 2,
            "spark_fruit": 3,
            "moon_biscuit": 1,
            "repair_gel": 1,
        }
    )
    owned_relics: list[str] = field(
        default_factory=lambda: ["ember_core", "echo_lens", "anchor_sigil"]
    )
    equipped_relic: str | None = "ember_core"
    last_updated: float = field(default_factory=time.time)
    last_actions: dict[str, float] = field(default_factory=dict)

    @property
    def xp_to_next_level(self) -> int:
        return 80 + self.level * 35

    @property
    def xp_progress(self) -> float:
        return clamp(self.xp / self.xp_to_next_level, 0.0, 1.0)

    @property
    def mood(self) -> str:
        if self.health < 30:
            return "UNWELL"
        if self.fullness < 25:
            return "HUNGRY"
        if self.energy < 25:
            return "TIRED"
        if self.joy < 30:
            return "LONELY"
        if min(self.energy, self.fullness, self.joy) >= 82:
            return "THRIVING"
        if self.bond >= 40:
            return "DEVOTED"
        return "CURIOUS"

    def energy_cap(self, relic: RelicDefinition | None = None) -> float:
        return 100.0 + (relic.energy_cap_bonus if relic else 0)

    def apply_elapsed_time(self, seconds: float, relic: RelicDefinition | None = None) -> None:
        """Apply capped offline/active decay without punishing long absences."""

        seconds = clamp(seconds, 0.0, 8 * 60 * 60)
        decay = relic.decay_multiplier if relic else 1.0
        self.energy = clamp(self.energy - (seconds / 180.0) * decay, 0, self.energy_cap(relic))
        self.fullness = clamp(self.fullness - (seconds / 150.0) * decay)
        self.joy = clamp(self.joy - (seconds / 300.0) * decay)
        if self.fullness < 12:
            self.health = clamp(self.health - seconds / 360.0)
        self.last_updated = time.time()

    def gain_xp(self, amount: int, relic: RelicDefinition | None = None) -> int:
        multiplier = relic.xp_multiplier if relic else 1.0
        gained = max(0, round(amount * multiplier))
        self.xp += gained
        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            self.health = clamp(self.health + 12)
            self.energy = clamp(self.energy + 18, 0, self.energy_cap(relic))
        return gained

    def use_item(self, item: ItemDefinition, relic: RelicDefinition | None = None) -> ActionResult:
        quantity = self.inventory.get(item.item_id, 0)
        if quantity <= 0:
            return ActionResult(False, f"NO {item.name} REMAINING")
        if not item.usable:
            return ActionResult(False, f"{item.name} IS A CRAFTING MATERIAL")

        care = relic.care_multiplier if relic else 1.0
        self.energy = clamp(self.energy + item.energy * care, 0, self.energy_cap(relic))
        self.fullness = clamp(self.fullness + item.fullness * care)
        self.joy = clamp(self.joy + item.joy * care)
        self.health = clamp(self.health + item.health * care)
        self.bond += item.bond + (relic.bond_bonus if relic else 0)
        self.inventory[item.item_id] = quantity - 1
        if self.inventory[item.item_id] <= 0:
            del self.inventory[item.item_id]
        gained = self.gain_xp(4, relic)
        self.total_actions += 1
        return ActionResult(True, f"USED {item.name}", gained)

    def perform_action(
        self,
        action: str,
        relic: RelicDefinition | None = None,
        *,
        now: float | None = None,
        rng: random.Random | None = None,
        reward_pool: tuple[str, ...] = (),
    ) -> ActionResult:
        now = time.time() if now is None else now
        rng = rng or random.Random()
        action = action.upper()
        rules = {
            "PLAY": {"cooldown": 8, "energy": -10, "fullness": -5, "joy": 20, "health": 0, "bond": 3, "xp": 12},
            "REST": {"cooldown": 10, "energy": 32, "fullness": -4, "joy": 3, "health": 5, "bond": 1, "xp": 6},
            "TRAIN": {"cooldown": 12, "energy": -18, "fullness": -9, "joy": -2, "health": 2, "bond": 2, "xp": 24},
            "EXPLORE": {"cooldown": 15, "energy": -14, "fullness": -8, "joy": 10, "health": 0, "bond": 2, "xp": 18},
            "COMFORT": {"cooldown": 5, "energy": 1, "fullness": 0, "joy": 10, "health": 1, "bond": 4, "xp": 4},
        }
        if action not in rules:
            return ActionResult(False, "UNKNOWN CARE ACTION")

        rule = rules[action]
        last_action = self.last_actions.get(action)
        if last_action is not None:
            remaining = rule["cooldown"] - (now - last_action)
            if remaining > 0:
                return ActionResult(False, f"{action} READY IN {math.ceil(remaining)}S")
        if rule["energy"] < 0 and self.energy < abs(rule["energy"]):
            return ActionResult(False, "NYX NEEDS REST")
        if rule["fullness"] < 0 and self.fullness < abs(rule["fullness"]):
            return ActionResult(False, "NYX NEEDS FOOD")

        care = relic.care_multiplier if relic else 1.0
        self.energy = clamp(self.energy + rule["energy"], 0, self.energy_cap(relic))
        self.fullness = clamp(self.fullness + rule["fullness"])
        self.joy = clamp(self.joy + rule["joy"] * care)
        self.health = clamp(self.health + rule["health"] * care)
        self.bond += rule["bond"] + (relic.bond_bonus if relic else 0)
        gained = self.gain_xp(rule["xp"], relic)
        self.last_actions[action] = now
        self.total_actions += 1

        reward = None
        if action == "EXPLORE" and reward_pool:
            find_chance = 0.42 + (relic.explore_find_bonus if relic else 0.0)
            if rng.random() < find_chance:
                reward = rng.choice(reward_pool)
                self.inventory[reward] = self.inventory.get(reward, 0) + 1

        message = f"{action} COMPLETE"
        if reward:
            message += " // ITEM FOUND"
        return ActionResult(True, message, gained, reward)

    def equip(self, relic_id: str) -> ActionResult:
        if relic_id not in self.owned_relics:
            return ActionResult(False, "RELIC NOT OWNED")
        if self.equipped_relic == relic_id:
            self.equipped_relic = None
            return ActionResult(True, "RELIC UNEQUIPPED")
        self.equipped_relic = relic_id
        return ActionResult(True, "RELIC EQUIPPED")

    def craft_relic(self, recipe: RelicRecipe, relic: RelicDefinition) -> ActionResult:
        if relic.relic_id in self.owned_relics:
            return ActionResult(False, f"{relic.name} ALREADY OWNED")
        missing = [
            f"{item_id.replace('_', ' ').upper()} x{quantity}"
            for item_id, quantity in recipe.ingredients.items()
            if self.inventory.get(item_id, 0) < quantity
        ]
        if missing:
            return ActionResult(False, f"NEED {missing[0]}")
        for item_id, quantity in recipe.ingredients.items():
            remaining = self.inventory.get(item_id, 0) - quantity
            if remaining:
                self.inventory[item_id] = remaining
            else:
                self.inventory.pop(item_id, None)
        self.owned_relics.append(relic.relic_id)
        self.total_actions += 1
        gained = self.gain_xp(30)
        return ActionResult(True, f"CRAFTED {relic.name}", gained)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Voidling":
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        clean = {key: value for key, value in data.items() if key in allowed}
        profile = cls(**clean)
        profile.energy = clamp(float(profile.energy), 0, 150)
        profile.fullness = clamp(float(profile.fullness))
        profile.joy = clamp(float(profile.joy))
        profile.health = clamp(float(profile.health))
        profile.level = max(1, int(profile.level))
        profile.xp = max(0, int(profile.xp))
        profile.bond = max(0, int(profile.bond))
        return profile
