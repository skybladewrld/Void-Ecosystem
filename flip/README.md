# Void Flip

Void Flip is the portable handheld in the Void Ecosystem. Version 0.2.1 focuses on making the companion and device simulation real before game production begins.

## What v0.2.1 includes

- Balanced dual-screen chassis with equal-width top and bottom halves
- Persistent Voidling energy, fullness, joy, health, bond, XP, and levels
- Five care routines with costs, effects, cooldowns, exploration drops, and resource checks
- Seven defined items, six effect-bearing relics, and three material-based relic recipes
- Usable inventory, equip/unequip controls, a workshop, and journal achievements
- A live battery simulation that drains, charges, autosaves, and sits behind a Raspberry Pi-ready adapter
- Interactive scanline, animation, status-detail, and simulated-charger settings
- A game-by-game production roadmap that does not label unfinished prototypes as playable
- Void Merge 2048 with complete board rules, pause, restart, end states, and saved high score

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

## Controls

| Action | Keys | Simulated control |
| --- | --- | --- |
| Navigate | Arrow keys or W/A/S/D | D-pad |
| Select | Enter or Space | A button |
| Back | Escape or Backspace | B button |
| Pause | Enter, Space, or P during Void Merge | Start button |
| Restart | R during Void Merge | Restart shortcut |
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
- `src/persistence.py` — versioned atomic local saves
- `src/theme.py` — shared visual primitives
- `tests/test_navigation.py` — headless navigation, simulation, save, and rendering checks

The current interface is drawn procedurally and needs no external assets.
