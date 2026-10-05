# Void Ecosystem

Void Ecosystem is a planned family of portable, local-first devices built around games, companions, multiplayer, trading, and creative tools. The current build is **Void Flip v0.3.1 — Depth & Polish**.

## The devices

- **Void Flip** — a portable dual-screen handheld with games, emulators, social features, settings, and a Voidling companion.
- **Void Node** — an optional local server for larger multiplayer sessions and validated trading.
- **Void Deck** — a future cyberdeck-style device combining Flip and Node capabilities with development tools.

## Current prototype

The current Windows desktop simulator uses Python and Pygame Community Edition. It models the Flip's balanced clamshell body, non-touch top display, smaller bottom companion display, D-pad, and face buttons. It stays lightweight and hardware-agnostic so the interface can later move to Raspberry Pi-class hardware.

![Void Flip desktop simulator](docs/void-flip-v0.2.png)

From the repository root:

```powershell
py -m pip install -r requirements.txt
py flip/src/main.py
```

## Project status

Void Flip v0.3.1 turns the Living System into a more coherent handheld shell. Nyx uses five focused tabs, game detail pages expose mastery and challenges before launch, Market purchases require confirmation, scrollable views retain their selection through layered Back navigation, and every major module has useful lower-screen context.

Blackglass now presents the human side at the bottom, explains mandatory captures, highlights capturing pieces and destinations, provides a rules screen, delays CPU input only long enough to show thinking feedback, and exposes complete match telemetry.

Three complete games are included: **Void Merge 2048**, **Signal Serpent**, and **Blackglass Checkers**. Blackglass supports a lightweight Easy/Normal/Hard CPU and reward-free local hot-seat play. Every rewarded game reports results through the centralized, duplicate-safe trust boundary instead of editing profile currency directly.

See [the v0.3.1 release notes](docs/v0.3.1.md), [community game API design](docs/game-api.md), [game roadmap](docs/game-roadmap.md), [simulator details](flip/README.md), and [architecture](docs/architecture.md).

Flux is fictional in-device currency only. It cannot be purchased with real money or redeemed for real-world value.
