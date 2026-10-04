# Void Ecosystem Architecture

## Guiding idea

Each device has a clear job and communicates through documented interfaces. Void Flip must work on its own; the network expands its abilities rather than becoming a requirement.

## Device relationships

**Void Flip** owns its interface, local games, emulator launchers, settings, and local Voidling. Two Flips should eventually support direct local play through a transport-neutral session interface.

**Void Node** is optional infrastructure for discovery, larger multiplayer sessions, trades, synchronization, and validation. It must not become a silent single-player dependency.

**Void Deck** comes later and should consume the same documented protocols rather than receive hidden privileged access.

## Current v0.2 layers

```text
Desktop OS
    ↓
Pygame window + keyboard input + desktop hardware adapter
    ↓
Void Flip navigation + versioned local profile store
    ↓
Voidling rules/content + top and bottom display renderers
```

Input mapping, simulation rules, content definitions, persistence, hardware telemetry, and drawing are separate. The `HardwareAdapter` contract lets a Raspberry Pi implementation replace simulated battery and temperature readings without rewriting the shell or Voidling. A future GPIO/controller adapter can feed the same named actions currently produced by keyboard events.

The v0.2 Core Loop adds a trusted systems layer between games and profile state. Built-in games return immutable result records; `CoreLoop` calculates and applies rewards, advances daily quests, records activity, checks level unlocks, and rejects already-claimed run IDs. Economy, quest, reward, progression, notification, and profile logic live under `flip/src/systems/` and remain independent from Pygame rendering.

The intended hardware direction is:

```text
Raspberry Pi OS Lite / Linux
    ↓
Void system services and hardware adapters
    ↓
Void Shell
    ↓
Games / emulators / Voidling / networking
```

A managed boot-to-shell setup on a maintained Linux base is the current direction. Real battery percentage should come from a supported fuel-gauge/UPS board; CPU voltage is not a trustworthy charge estimate.

The desktop battery is deliberately simulated: each normal launch starts at 100%, drains at one percentage point per 80 seconds, and charges at one point per 12 seconds when the simulated charger is enabled. A command-line override supports low-power tests. Those rates are development feedback, not final hardware power estimates.

## Future boundaries

- A platform-owned launcher starts games and passes only approved context.
- Games request rewards or state changes through a controlled Void API.
- Trusted profile and ownership data stay outside game directories.
- Networking uses versioned messages so Flip, Node, and Deck releases can evolve independently.
- Bottom-screen touch input is optional and not embedded in core game logic.
