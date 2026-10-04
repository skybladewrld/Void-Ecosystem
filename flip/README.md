# Void Flip

Void Flip is the portable handheld in the Void Ecosystem. Version 0.2 grows the runnable desktop simulator into the first interactive shell while the physical screens, controls, and Raspberry Pi-class computer are still being designed.

## What v0.2 includes

- Balanced dual-screen chassis with equal-width top and bottom halves
- Polished home dashboard and populated Games, Emulators, Friends, Trading, and Settings modules
- `Signal Catch`, a playable built-in arcade prototype with score and miss tracking
- Interactive scanline, animation, and status-detail settings
- Context-aware bottom display for the Voidling, game telemetry, and setting previews
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

On the home screen, Up/Down moves through the menu. Module lists also use Up/Down. Select launches the ready game or toggles a setting; Back moves up one level. In Signal Catch, move left and right to catch the falling signal.

## Source layout

- `src/main.py` — launch entry point and command-line options
- `src/app.py` — application loop, input mapping, navigation, and screen composition
- `src/content.py` — library, emulator, friend, trade, and setting content
- `src/theme.py` — shared colors, typography helpers, panels, and sharp corner accents
- `src/models.py` — expandable data models for the Voidling and inventory
- `tests/test_navigation.py` — headless state/navigation checks

The empty asset folders are ready for later sprites, sound effects, and licensed fonts. v0.1 draws everything procedurally and needs no external assets.
