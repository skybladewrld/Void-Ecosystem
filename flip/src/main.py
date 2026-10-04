"""Launch Void Flip v0.2.1 from the repository root with `py flip/src/main.py`."""

import argparse
import os
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Void Flip v0.2.1 desktop simulator")
    parser.add_argument("--no-splash", action="store_true", help="skip the startup splash")
    parser.add_argument("--smoke-test", action="store_true", help="run a short headless navigation check")
    parser.add_argument("--screenshot", type=Path, help="save a home-screen screenshot and exit")
    parser.add_argument("--battery", type=float, metavar="PERCENT", help="override the starting battery from 0 to 100")
    args = parser.parse_args()
    if args.battery is not None and not 0 <= args.battery <= 100:
        parser.error("--battery must be between 0 and 100")
    return args


def run_smoke_test():
    """Exercise the same state changes as real keys without a visible window."""

    from app import MENU_ITEMS, VoidFlipApp

    app = VoidFlipApp(show_splash=False, persist=False)
    assert app.page == "HOME"
    for index, item in enumerate(MENU_ITEMS):
        app.selected_index = index
        app.handle_action("select")
        assert app.page == item
        app.handle_action("back")
        assert app.page == "HOME"
    app.handle_action("down")
    assert app.selected_index == 0
    app.handle_action("up")
    assert app.selected_index == len(MENU_ITEMS) - 1
    assert app.voidling.name and 0.0 <= app.voidling.xp_progress <= 1.0
    app.open_page("VOIDLING")
    app.handle_action("select")
    assert app.page == "CARE"
    before_actions = app.voidling.total_actions
    app.handle_action("select")
    assert app.voidling.total_actions == before_actions + 1
    app.handle_action("back")
    assert app.page == "VOIDLING"
    app.open_page("GAMES")
    app.handle_action("select")
    assert app.page == "VOID MERGE 2048"
    app.void_merge.board = [[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    app.handle_action("left")
    assert app.void_merge.score == 4
    before_battery = app.hardware.snapshot().battery_percent
    app.hardware.update(80)
    assert app.hardware.snapshot().battery_percent < before_battery
    app.handle_action("quit")
    assert not app.running
    import pygame

    pygame.quit()
    print("Void Flip v0.2.1 smoke test passed: companion loop, hardware telemetry, navigation, and Void Merge are ready.")


def main():
    args = parse_args()
    if args.smoke_test or args.screenshot:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    if args.smoke_test:
        run_smoke_test()
        return

    from app import VoidFlipApp

    app = VoidFlipApp(
        show_splash=not args.no_splash and args.screenshot is None,
        battery_percent=args.battery,
    )
    if args.screenshot:
        app.run(max_frames=2, screenshot=args.screenshot.resolve())
    else:
        app.run()


if __name__ == "__main__":
    main()
