# Void Ecosystem

Void Ecosystem is a planned family of portable, local-first devices built around games, companions, multiplayer, trading, and creative tools. The project is currently developing **Void Flip v0.2.1**.

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

Void Flip v0.2.1 replaces the throwaway arcade prototype with the first real platform system: a persistent Voidling with changing needs, care cooldowns, usable items, exploration rewards, relic effects, crafting recipes, achievements, XP, levels, and bond progression. Device power now drains and charges in the desktop simulator through the same adapter boundary intended for Raspberry Pi hardware.

The first complete built-in game is **Void Merge 2048**, with correct once-per-move merging, scoring, tile spawning, pause/restart controls, win/loss detection, and a persistent high score.

The game library is an honest production roadmap, not a menu of fake launch buttons. Each game will be implemented and tested as a complete vertical slice before it is marked playable. See [the game roadmap](docs/game-roadmap.md), [Voidling system design](docs/voidling-system.md), [simulator details](flip/README.md), and [architecture](docs/architecture.md).

Void credits are fictional in-device currency only. They will never be purchasable with real money or redeemable for real-world value.
