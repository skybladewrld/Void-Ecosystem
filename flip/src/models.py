"""Small data models owned by the Void Flip interface."""

from dataclasses import dataclass, field


@dataclass
class InventoryItem:
    """A future usable item shown in the bottom-screen mini inventory."""

    name: str
    quantity: int = 1


@dataclass
class Voidling:
    """The v0.1 companion state, kept separate from rendering for future persistence."""

    name: str = "Nyx"
    level: int = 3
    xp: int = 42
    xp_to_next_level: int = 100
    energy: int = 78
    mood: str = "CURIOUS"
    inventory: list[InventoryItem] = field(
        default_factory=lambda: [
            InventoryItem("VOID SHARD", 2),
            InventoryItem("SPARK FRUIT", 1),
        ]
    )

    @property
    def xp_progress(self) -> float:
        if self.xp_to_next_level <= 0:
            return 1.0
        return max(0.0, min(1.0, self.xp / self.xp_to_next_level))

    @property
    def energy_progress(self) -> float:
        return max(0.0, min(1.0, self.energy / 100))
