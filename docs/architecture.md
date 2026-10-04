# Void Ecosystem Architecture

## Guiding idea

Each device should have a clear job and communicate through documented interfaces. Void Flip must work on its own; the network expands its abilities rather than becoming a requirement.

## Device relationships

### Void Flip

Flip is the primary portable device. It owns its interface, local games, emulator launchers, settings, and local Voidling experience. A Flip should boot directly into the future Void Shell and remain useful offline.

Two Flips should eventually support direct local connections for two-player games without requiring a Node. Possible transports include local Wi-Fi, Bluetooth, or a physical cable if the final hardware supports a safe and reliable data link. Gameplay code should use a transport-neutral session interface so the transport can change later.

### Void Node

Node is optional infrastructure. It can provide neutral hosted services where a trusted third party is helpful: discovery, multiplayer above two players, trades, synchronization, and validation. Node must not become a silent dependency for ordinary single-player use.

### Void Deck

Deck comes later. It may combine portable features with Node services and development tools, but should consume the same documented protocols instead of receiving hidden privileged access.

## Current v0.2 layers

```text
Desktop operating system
        ↓
Pygame window and keyboard input
        ↓
Void Flip application state
        ↓
Top-display modules + bottom-display Voidling context
```

The simulator keeps input handling, state, content data, and drawing conceptually separate. Later, keyboard events can be replaced by GPIO/controller events, while the same interface state and display renderers target physical displays. The built-in Signal Catch game proves that the shell can hand off controls and both displays to an interactive module without introducing a hardware dependency.

The intended hardware direction is:

```text
Raspberry Pi OS Lite / Linux
        ↓
Void system services
        ↓
Void Shell
        ↓
Games / emulators / Voidling / networking
```

Building a custom kernel or Linux distribution is not a v0.1 goal. A managed boot-to-shell setup on a maintained Linux base is simpler to update and secure.

## Future boundaries

- A platform-owned launcher starts games and passes only approved context.
- Games request rewards or state changes through a controlled Void API.
- Trusted profile and ownership data stay outside game directories.
- Networking uses versioned messages so Flip, Node, and Deck releases can evolve independently.
- Bottom-screen touch input is an optional input source, not an assumption embedded in game logic.
