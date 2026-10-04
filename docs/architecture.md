# Void Ecosystem Architecture

## Guiding idea

Each device has a clear job and communicates through documented interfaces. Void Flip must work on its own; the network expands its abilities rather than becoming a requirement.

## Device relationships

**Void Flip** owns its interface, local games, emulator launchers, settings, and local Voidling. Two Flips should eventually support direct local play through a transport-neutral session interface.

**Void Node** is optional infrastructure for discovery, larger multiplayer sessions, trades, synchronization, and validation. It must not become a silent single-player dependency.

**Void Deck** comes later and should consume the same documented protocols rather than receive hidden privileged access.

## Current v0.2.1 layers

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

The desktop battery is deliberately simulated: it drains at one percentage point per 80 seconds and charges at one point per 12 seconds. Its last value and charger setting are persisted. Those rates are development feedback, not final hardware power estimates.

## Future boundaries

- A platform-owned launcher starts games and passes only approved context.
- Games request rewards or state changes through a controlled Void API.
- Trusted profile and ownership data stay outside game directories.
- Networking uses versioned messages so Flip, Node, and Deck releases can evolve independently.
- Bottom-screen touch input is optional and not embedded in core game logic.
