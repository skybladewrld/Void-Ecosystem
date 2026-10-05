# Void Flip

Void Flip is the portable handheld in the Void Ecosystem. Version 0.3 deepens its connected progression loop into a Living System.

## What v0.3 adds

- Contextual Nyx behavior states, thoughts, blinking, eye movement, sleep motion, and reactions
- Blackglass Checkers with standard 8x8 movement, forced captures, multi-jumps, kings, terminal states, three CPU difficulties, and local hot-seat play
- Persistent mastery for all three games and twelve one-time game challenges
- Two deterministic weekly quests plus forgiving daily-completion streaks
- Void Codex discovery tracking across items, materials, relics, games, achievements, and mastery badges
- 22 categorized achievements and a complete local Profile overview
- Priority notification queue with a bounded 20-entry Notification Center
- Optional procedural UI audio that safely disables itself when audio hardware is unavailable
- Hardware Adapter v2 metadata, named input actions, and future Void Link data contracts
- Save-schema v3 migration that preserves v2 progress

## Existing connected systems

- Balanced dual-screen chassis with equal-width top and bottom halves
- Persistent Voidling energy, fullness, joy, health, bond, XP, and levels
- Five care routines with costs, effects, cooldowns, exploration drops, and resource checks
- Seven defined items, six effect-bearing relics, and three material-based relic recipes
- Usable inventory, equip/unequip controls, a workshop, and journal achievements
- A live battery simulation that drains, charges, autosaves, and sits behind a Raspberry Pi-ready adapter
- Interactive scanline, animation, status-detail, and simulated-charger settings
- A game-by-game production roadmap that does not label unfinished prototypes as playable
- Void Merge 2048 with complete board rules, pause, restart, end states, and saved high score
- Signal Serpent with growth, combos, hazards, speed tiers, shards, and persistent statistics
- Flux economy and a six-item Void Market with controlled Mystery Cache loot
- Three date-based daily quests with automatic progress and reward claiming
- Level-derived module unlocks and advanced-relic gating
- Centralized, duplicate-safe game rewards with relic modifiers
- Sliding notifications and a rolling 75-event activity history
- Contextual lower-screen views for Home, games, quests, Market, Workshop, and Settings
- Save-schema v3 migration with atomic writes and `.bak` recovery copies

The top display is treated as non-touch. The bottom display is a separate context area so touch input can be added later.

## Run from the repository root

```powershell
py -m pip install -r requirements.txt
py flip/src/main.py
```

To test critical-power behavior at 0.1%:

```powershell
py flip/src/main.py --battery 0.1 --no-splash
```

`--battery` accepts any starting percentage from `0` through `100` and overrides the saved charge for that launch.

Use `--scale 0.75` through `--scale 2.0` to resize the desktop window while preserving the logical top/bottom display layout.

Every normal desktop simulator launch begins at 100%. Later Raspberry Pi hardware will replace that temporary assumption with live charge data from a supported fuel-gauge or UPS board through the existing hardware adapter.

## Controls

| Action | Keys | Simulated control |
| --- | --- | --- |
| Navigate | Arrow keys or W/A/S/D | D-pad |
| Select | Enter or Space | A button |
| Back | Escape or Backspace | B button |
| Pause | Enter, Space, or P during a game | Start button |
| Restart | R during a game | Restart shortcut |
| Blackglass mode | X | CPU / local hot-seat |
| Blackglass CPU | Y | Easy / Normal / Hard |
| Quit | Q | System shortcut |

Select performs a care action, uses an item, equips a relic, crafts a recipe, or toggles a setting depending on the page. Back moves up one level.

Progress is saved automatically to `%APPDATA%\VoidEcosystem\flip-profile.json` on Windows. Use **Settings → Sim Charger** to see the battery reverse from draining to charging.

## Source layout

- `src/main.py` — launch entry point and command-line options
- `src/app.py` — application loop, input mapping, navigation, and screen composition
- `src/content.py` — platform-owned items, relics, recipes, and library content
- `src/models.py` — Voidling simulation and progression rules
- `src/hardware.py` — simulated telemetry and the future hardware adapter contract
- `src/games/void_merge.py` — tested Void Merge 2048 rules
- `src/games/signal_serpent.py` — tested Signal Serpent rules
- `src/games/blackglass.py` — pure Checkers rules, game state, and CPU selection
- `src/systems/` — behavior, Codex, mastery, achievements, quests, rewards, economy, and profile state
- `src/input.py` / `src/audio.py` — named actions and optional procedural feedback
- `src/shared/void_link.py` — data-only future networking contracts
- `src/persistence.py` — versioned atomic local saves
- `src/theme.py` — shared visual primitives
- `tests/` — navigation/rendering plus pure economy, quest, migration, reward, and game-rule tests

The current interface is drawn procedurally and needs no external assets.
