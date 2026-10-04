# Void Ecosystem

Void Ecosystem is a planned family of portable, local-first devices built around games, companions, multiplayer, trading, and creative tools. The project is currently developing **Void Flip v0.2 — Core Loop**.

## The devices

- **Void Flip** — a portable dual-screen handheld with games, emulators, social features, settings, and a Voidling companion.
- **Void Node** — an optional local server for larger multiplayer sessions and validated trading.
- **Void Deck** — a future cyberdeck-style device combining Flip and Node capabilities with development tools.

## Current prototype

The current Windows desktop simulator uses Python and Pygame Community Edition. It models the Flip's balanced clamshell body, non-touch top display, smaller bottom companion display, D-pad, and face buttons. It stays lightweight and hardware-agnostic so the interface can later move to Raspberry Pi-class hardware.

![Void Flip v0.2 desktop simulator](docs/void-flip-v0.2.png)

From the repository root:

```powershell
py -m pip install -r requirements.txt
py flip/src/main.py
```

## Project status

Void Flip v0.2 connects its systems into a persistent play loop. Games award trusted XP, Flux, and materials; daily quests respond to real actions; the Void Market spends Flux; care, items, crafting, achievements, relics, notifications, unlocks, and activity history all feed the same profile.

Two complete games are included: **Void Merge 2048** and **Signal Serpent**. Both report results through a centralized, duplicate-safe reward boundary instead of editing profile currency directly.

See [the v0.2 release notes](docs/v0.2.md), [game roadmap](docs/game-roadmap.md), [Voidling system design](docs/voidling-system.md), [simulator details](flip/README.md), and [architecture](docs/architecture.md).

Flux is fictional in-device currency only. It cannot be purchased with real money or redeemed for real-world value.
