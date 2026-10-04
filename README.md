# Void Ecosystem

Void Ecosystem is a planned family of portable, local-first devices built around games, companions, multiplayer, trading, and creative tools. The project is currently developing **Void Flip v0.2**.

## The devices

- **Void Flip** — a portable dual-screen handheld. It works independently and hosts games, emulators, social features, settings, and a Voidling companion.
- **Void Node** — an optional local server for neutral shared services such as larger multiplayer sessions and validated trading.
- **Void Deck** — a future cyberdeck-style device combining Flip and Node capabilities with development tools.

## Current phase: Void Flip v0.2

The current prototype is a Windows desktop simulator built with Python and Pygame Community Edition (imported as `pygame`). This package has Windows builds for Python 3.14. The simulator models the Flip's balanced clamshell body, non-touch top display, smaller bottom companion display, D-pad, and face buttons. It is deliberately lightweight and hardware-agnostic so the interface can later move to Raspberry Pi-class hardware.

![Void Flip v0.2 desktop simulator](docs/void-flip-v0.2.png)

### Install

From the repository root:

```powershell
py -m pip install -r requirements.txt
```

### Run

```powershell
py flip/src/main.py
```

See [flip/README.md](flip/README.md) for controls and simulator details. Architecture and security direction live in [docs/architecture.md](docs/architecture.md) and [docs/security.md](docs/security.md).

## Project status

Void Flip v0.2 adds a playable built-in arcade prototype, interactive settings, richer module views, and context-aware bottom-screen information. It is still an early simulator, not a finished console or operating system. Emulators, accounts, networking, trusted trading, persistent progression, and hardware input drivers remain future work.

Void credits are fictional in-device currency only. They will never be purchasable with real money or redeemable for real-world value.
