"""Flux-only Void Market with a controlled loot table."""

from __future__ import annotations

import random
from dataclasses import dataclass

from systems.rewards import RewardBundle


@dataclass(frozen=True)
class MarketEntry:
    sku: str
    title: str
    price: int
    description: str
    item_id: str | None = None


@dataclass(frozen=True)
class PurchaseResult:
    success: bool
    message: str
    reward: RewardBundle = RewardBundle()


MARKET_STOCK = (
    MarketEntry("spark_fruit", "SPARK FRUIT", 25, "Reliable food and a small energy lift.", "spark_fruit"),
    MarketEntry("moon_biscuit", "MOON BISCUIT", 40, "A joyful treat Nyx especially likes.", "moon_biscuit"),
    MarketEntry("static_toy", "STATIC TOY", 60, "A high-joy care item.", "static_toy"),
    MarketEntry("starlight_tea", "STARLIGHT TEA", 75, "Restores energy for longer sessions.", "starlight_tea"),
    MarketEntry("repair_gel", "REPAIR GEL", 90, "Restores health after hard training.", "repair_gel"),
    MarketEntry("mystery_cache", "MYSTERY CACHE", 150, "Controlled cache of items or materials."),
)

MARKET_BY_SKU = {entry.sku: entry for entry in MARKET_STOCK}
MYSTERY_CACHE_LOOT = (
    RewardBundle(items={"spark_fruit": 2}),
    RewardBundle(items={"moon_biscuit": 1, "void_shard": 1}),
    RewardBundle(items={"starlight_tea": 1}),
    RewardBundle(items={"repair_gel": 1}),
    RewardBundle(items={"void_shard": 2}),
    RewardBundle(items={"prism_seed": 1}),
)


def buy(profile, sku: str, rng: random.Random | None = None) -> PurchaseResult:
    entry = MARKET_BY_SKU.get(sku)
    if not entry:
        return PurchaseResult(False, "UNKNOWN MARKET ITEM")
    if profile.flux < entry.price:
        return PurchaseResult(False, f"NEED {entry.price - profile.flux} MORE FLUX")
    profile.flux -= entry.price
    if entry.item_id:
        reward = RewardBundle(items={entry.item_id: 1})
    else:
        reward = (rng or random.Random()).choice(MYSTERY_CACHE_LOOT)
    return PurchaseResult(True, f"PURCHASED {entry.title}", reward)
