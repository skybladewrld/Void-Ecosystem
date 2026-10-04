# Void Flip

Void Flip is the portable handheld in the Void Ecosystem. Version 0.1 is a runnable desktop simulator for exploring the interface before the physical screens, controls, and Raspberry Pi-class computer are finalized.

## What v0.1 includes

- VOID startup splash and lightweight transition
- Dual-screen clamshell visual with drawn D-pad and A/B/X/Y controls
- Home menu and working placeholder pages for Games, Emulators, Friends, Trading, and Settings
- Bottom-screen Voidling companion with name, level, XP, energy, mood, mini inventory, and idle animation
- Keyboard input separated from rendering so hardware input can replace it later

The top display is treated as non-touch. The bottom display is structured as a separate context area so touch input can be added later.

## Run from the repository root

```powershell
py -m pip install -r requirements.txt
py flip/src/main.py
```

## Controls

| Action | Keys | Simulated control |
| --- | --- | --- |
| Navigate | Arrow keys or W/A/S/D | D-pad |
| Select | Enter or Space | A button |
| Back | Escape or Backspace | B button |
| Quit | Q | System shortcut |

On the home screen, Up/Down moves through the menu. Selecting a section opens its module page; Back returns home.

## Source layout

- `src/main.py` — launch entry point and command-line options
- `src/app.py` — application loop, input mapping, navigation, and screen composition
- `src/theme.py` — shared colors, typography helpers, panels, and sharp corner accents
- `src/models.py` — expandable data models for the Voidling and inventory
- `tests/test_navigation.py` — headless state/navigation checks

The empty asset folders are ready for later sprites, sound effects, and licensed fonts. v0.1 draws everything procedurally and needs no external assets.
