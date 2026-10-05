"""Void Flip shell, companion simulation, navigation, and rendering."""

from __future__ import annotations

import math
import time
from pathlib import Path

import pygame

from audio import AudioManager
from content import (
    CARE_ACTIONS,
    EMULATOR_SYSTEMS,
    EXPLORE_REWARDS,
    FRIEND_SLOTS,
    GAME_LIBRARY,
    ITEMS,
    RELICS,
    RELIC_RECIPES,
    SETTING_LABELS,
)
from hardware import DesktopHardwareAdapter
from games.blackglass import BlackglassGame, legal_moves
from games.void_merge import VoidMergeGame
from games.signal_serpent import SignalSerpentGame
from input import Action, keyboard_action
from models import Voidling
from persistence import ProfileStore
from systems.core_loop import CoreLoop
from systems.achievements import ACHIEVEMENTS
from systems.behavior import NyxBehavior
from systems.codex import completion, discover
from systems.economy import MARKET_STOCK
from systems.notifications import NotificationCenter
from systems.mastery import CHALLENGES, GAME_TITLES, level_for_xp, progress_for_xp
from systems.profile import CoreProfile
from systems.progression import UNLOCK_LEVELS, is_unlocked
from systems.quests import QUESTS_BY_ID
from systems.rewards import GameResult, game_reward, reward_tier
from systems.weekly import WEEKLY_BY_ID
from theme import (
    BLACK, BODY, BODY_EDGE, GREEN, MUTED, PANEL, PANEL_LIGHT, PURPLE,
    PURPLE_DARK, PURPLE_LIGHT, SCREEN, WHITE, draw_meter, draw_panel,
    draw_text, make_fonts,
)


WINDOW_SIZE = (1200, 900)
CHASSIS_LEFT = 92
CHASSIS_WIDTH = 1016
TOP_BODY = pygame.Rect(CHASSIS_LEFT, 35, CHASSIS_WIDTH, 472)
BOTTOM_BODY = pygame.Rect(CHASSIS_LEFT, 520, CHASSIS_WIDTH, 342)
TOP_SCREEN = pygame.Rect(170, 78, 860, 386)
BOTTOM_SCREEN = pygame.Rect(405, 572, 390, 242)
MENU_ITEMS = ("GAMES", "VOIDLING", "QUESTS", "MARKET", "WORKSHOP", "FRIENDS", "TRADING", "EMULATORS", "SETTINGS")
VOIDLING_SECTIONS = ("CARE", "INVENTORY", "RELICS", "WORKSHOP", "MASTERY", "CHALLENGES", "CODEX", "PROFILE", "JOURNAL", "NOTIFICATIONS")
PAGE_PARENTS = {
    "VOIDLING": "HOME",
    "CARE": "VOIDLING",
    "INVENTORY": "VOIDLING",
    "RELICS": "VOIDLING",
    "WORKSHOP": "VOIDLING",
    "JOURNAL": "VOIDLING",
    "MASTERY": "VOIDLING",
    "CHALLENGES": "VOIDLING",
    "CODEX": "VOIDLING",
    "PROFILE": "VOIDLING",
    "NOTIFICATIONS": "VOIDLING",
    "GAMES": "HOME",
    "QUESTS": "HOME",
    "MARKET": "HOME",
    "EMULATORS": "HOME",
    "FRIENDS": "HOME",
    "TRADING": "HOME",
    "SETTINGS": "HOME",
    "VOID MERGE 2048": "GAMES",
    "SIGNAL SERPENT": "GAMES",
    "BLACKGLASS CHECKERS": "GAMES",
}


def fit_text(font, value, max_width):
    """Keep dense console labels inside their assigned column."""

    value = str(value)
    if font.size(value)[0] <= max_width:
        return value
    suffix = "..."
    while value and font.size(value + suffix)[0] > max_width:
        value = value[:-1]
    return value + suffix


class VoidFlipApp:
    """Hardware-agnostic interface with trusted, persistent companion state."""

    def __init__(self, *, show_splash=True, persist=True, save_path=None, battery_percent=None, window_scale=1.0):
        pygame.init()
        pygame.display.set_caption("Void Flip v0.3 — Living System")
        self.window_scale = max(0.5, min(2.0, float(window_scale)))
        self.window = pygame.display.set_mode(tuple(round(value * self.window_scale) for value in WINDOW_SIZE))
        self.surface = pygame.Surface(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.fonts = make_fonts()
        self.running = True
        self.page = "HOME"
        self.page_stack = []
        self.selected_index = 0
        self.module_index = 0
        self.started_at = time.monotonic()
        self.show_splash = show_splash
        self.splash_duration = 2.15
        self.transition = 0.0
        self.toast = "SYSTEM READY"
        self.toast_timer = 0.0
        self.profile_tick = 0.0
        self.autosave_tick = 0.0
        self.quest_tick = 0.0
        self.low_battery_notified = False
        self._notification_token = None

        self.store = ProfileStore(save_path) if persist else None
        payload = self.store.load() if self.store else {}
        self.settings = {
            "SCANLINES": True,
            "ANIMATIONS": True,
            "SOUND": True,
            "STATUS DETAIL": True,
            "SIM CHARGER": False,
        }
        self.settings.update({key: bool(value) for key, value in payload.get("settings", {}).items() if key in self.settings})
        self.voidling = Voidling.from_dict(payload.get("voidling", {})) if payload.get("voidling") else Voidling()
        self.core_profile = CoreProfile.from_payload(payload)
        self.game_stats = self.core_profile.game_stats
        self.void_merge = VoidMergeGame()
        self.signal_serpent = SignalSerpentGame()
        self.blackglass = BlackglassGame()
        self.notifications = NotificationCenter(self.core_profile.notification_history)
        self.core = CoreLoop(self.core_profile, self.voidling, self.notifications)
        self.behavior = NyxBehavior(self.core_profile.behavior)
        self.audio = AudioManager(pygame)
        initial_battery = 100.0 if battery_percent is None else battery_percent
        self.hardware = DesktopHardwareAdapter(
            battery_percent=float(initial_battery),
            charging=self.settings["SIM CHARGER"],
        )
        elapsed = max(0.0, time.time() - self.voidling.last_updated)
        self.voidling.apply_elapsed_time(elapsed, self.current_relic())
        if self.store and self.store.last_error:
            self.show_toast("SAVE LOAD WARNING // DEFAULTS USED")

    def current_relic(self):
        return RELICS.get(self.voidling.equipped_relic)

    def save_state(self):
        if not self.store:
            return
        self.voidling.last_updated = time.time()
        self.core_profile.notification_history = self.notifications.history
        self.core_profile.behavior = self.behavior.to_dict()
        data = {
            "voidling": self.voidling.to_dict(),
            "settings": self.settings,
        }
        data.update(self.core_profile.to_payload())
        self.store.save(data)

    def handle_action(self, action):
        """Update state independently of keyboard, GPIO, or touch sources."""

        if self.settings.get("SOUND"):
            sound = "navigate" if action in ("up", "down", "left", "right") else "back" if action == "back" else "confirm" if action == "select" else None
            if sound:
                self.audio.play(sound)

        if action == "quit":
            self.save_state()
            self.running = False
            return
        if action == "back":
            if self.page == "VOID MERGE 2048":
                self.finalize_void_merge()
            elif self.page == "SIGNAL SERPENT":
                self.finalize_signal_serpent()
            elif self.page == "BLACKGLASS CHECKERS":
                self.finalize_blackglass()
            target = self.page_stack.pop() if self.page_stack else PAGE_PARENTS.get(self.page, "HOME")
            self.open_page(target, push=False)
            return

        if self.page == "HOME":
            self.handle_home_navigation(action)
        elif self.page == "VOIDLING":
            self.handle_list_navigation(action, len(VOIDLING_SECTIONS))
            if action == "select":
                self.open_page(VOIDLING_SECTIONS[self.module_index])
        elif self.page == "CARE":
            self.handle_list_navigation(action, len(CARE_ACTIONS))
            if action == "select":
                self.perform_care_action(CARE_ACTIONS[self.module_index][0])
        elif self.page == "INVENTORY":
            count = max(1, len(self.inventory_ids()))
            self.handle_list_navigation(action, count)
            if action == "select" and self.inventory_ids():
                self.use_selected_item()
        elif self.page == "RELICS":
            count = max(1, len(self.voidling.owned_relics))
            self.handle_list_navigation(action, count)
            if action == "select" and self.voidling.owned_relics:
                relic_id = self.voidling.owned_relics[self.module_index]
                result = self.voidling.equip(relic_id)
                self.show_toast(result.message)
                if result.success:
                    relic_name = RELICS[relic_id].name
                    verb = "Unequipped" if self.voidling.equipped_relic is None else "Equipped"
                    self.core_profile.add_activity("relic", f"{verb} {relic_name}")
                self.save_state()
        elif self.page == "WORKSHOP":
            self.handle_list_navigation(action, len(RELIC_RECIPES))
            if action == "select":
                recipe = RELIC_RECIPES[self.module_index]
                if self.module_index > 0 and not is_unlocked("advanced_relics", self.voidling.level):
                    self.show_toast(f"ADVANCED RELIC // LEVEL {UNLOCK_LEVELS['advanced_relics']}")
                    return
                old_level = self.voidling.level
                old_bond = self.voidling.bond
                result = self.voidling.craft_relic(recipe, RELICS[recipe.relic_id])
                message = result.message + (f" // +{result.xp_gained} XP" if result.success else "")
                self.show_toast(message)
                if result.success:
                    self.core_profile.add_activity("craft", result.message)
                    self.core_profile.profile_stats["crafted"] += 1
                    discover(self.core_profile, "relics", recipe.relic_id)
                    self.core.record_event("craft", 1)
                    self.core.record_event("xp_gained", result.xp_gained)
                    self.core.track_voidling_milestones(old_level, old_bond)
                    self.notifications.push("RELIC CRAFTED", RELICS[recipe.relic_id].name)
                    self.behavior.react("EXCITED")
                    self.save_state()
        elif self.page in ("JOURNAL", "MASTERY", "CHALLENGES", "CODEX", "PROFILE", "NOTIFICATIONS"):
            self.handle_list_navigation(action, len(self.voidling_rows()))
        elif self.page == "GAMES":
            self.handle_list_navigation(action, len(GAME_LIBRARY))
            if action == "select":
                game = GAME_LIBRARY[self.module_index]
                if game.game_id == "merge_2048" and game.playable:
                    self.open_page("VOID MERGE 2048")
                elif game.game_id == "signal_serpent" and game.playable:
                    if is_unlocked("signal_serpent", self.voidling.level):
                        self.open_page("SIGNAL SERPENT")
                    else:
                        self.show_toast(f"LOCKED // LEVEL {UNLOCK_LEVELS['signal_serpent']}")
                elif game.game_id == "blackglass" and game.playable:
                    self.open_page("BLACKGLASS CHECKERS")
                else:
                    self.show_toast(f"{game.title} // DEVELOPMENT QUEUE")
        elif self.page == "VOID MERGE 2048":
            self.handle_void_merge(action)
        elif self.page == "SIGNAL SERPENT":
            self.handle_signal_serpent(action)
        elif self.page == "BLACKGLASS CHECKERS":
            self.handle_blackglass(action)
        elif self.page == "QUESTS":
            self.handle_list_navigation(action, len(self.all_quests()))
        elif self.page == "MARKET":
            self.handle_list_navigation(action, len(MARKET_STOCK))
            if action == "select":
                if not is_unlocked("market", self.voidling.level):
                    self.show_toast(f"LOCKED // LEVEL {UNLOCK_LEVELS['market']}")
                else:
                    self.core.purchase(MARKET_STOCK[self.module_index].sku)
                    self.behavior.react("CURIOUS")
                    self.save_state()
        elif self.page == "SETTINGS":
            self.handle_list_navigation(action, len(SETTING_LABELS))
            if action in ("select", "left", "right"):
                self.toggle_setting(SETTING_LABELS[self.module_index])
        else:
            counts = {
                "EMULATORS": len(EMULATOR_SYSTEMS),
                "FRIENDS": len(FRIEND_SLOTS),
                "TRADING": max(1, len(self.inventory_ids())),
            }
            self.handle_list_navigation(action, counts[self.page])
            if action == "select":
                messages = {
                    "EMULATORS": "SETUP FLOW COMES AFTER VOIDLING CORE",
                    "FRIENDS": "DIRECT LINK SERVICE NOT ACTIVE",
                    "TRADING": "TRUSTED TRADE SERVICE NOT ACTIVE",
                }
                self.show_toast(messages[self.page])

    def handle_home_navigation(self, action):
        columns = 3
        if action == "x":
            self.open_page("VOID MERGE 2048")
        elif action == "y":
            self.open_page("SIGNAL SERPENT")
        elif action == "select_menu":
            self.open_page("BLACKGLASS CHECKERS")
        elif action == "left":
            self.selected_index = (self.selected_index - 1) % len(MENU_ITEMS)
        elif action == "right":
            self.selected_index = (self.selected_index + 1) % len(MENU_ITEMS)
        elif action == "up":
            self.selected_index = (self.selected_index - columns) % len(MENU_ITEMS)
        elif action == "down":
            self.selected_index = (self.selected_index + columns) % len(MENU_ITEMS)
        elif action == "select":
            page = MENU_ITEMS[self.selected_index]
            lock_id = {"MARKET": "market", "WORKSHOP": "workshop"}.get(page)
            if lock_id and not is_unlocked(lock_id, self.voidling.level):
                self.show_toast(f"LOCKED // LEVEL {UNLOCK_LEVELS[lock_id]}")
            else:
                self.open_page(page)

    def handle_void_merge(self, action):
        if action in ("up", "down", "left", "right"):
            self.void_merge.move(action)
            if self.void_merge.game_over:
                self.finalize_void_merge()
                self.show_toast("GRID LOCKED // ENTER TO RESTART")
        elif action == "select":
            if self.void_merge.game_over:
                self.finalize_void_merge()
                self.void_merge.new_game()
                self.show_toast("NEW GRID INITIALIZED")
            else:
                self.void_merge.paused = not self.void_merge.paused
                self.show_toast("PAUSED" if self.void_merge.paused else "RESUMED")
        elif action == "restart":
            self.finalize_void_merge()
            self.void_merge.new_game()
            self.show_toast("GRID RESTARTED")
        elif action == "pause":
            self.void_merge.paused = not self.void_merge.paused

    def finalize_void_merge(self):
        game = self.void_merge
        if game.reward_applied or game.moves <= 0:
            return False
        result = GameResult(
            reward_id=f"game:void_merge:{game.run_id}",
            game_id="void_merge",
            score=game.score,
            metrics={"highest_tile": game.highest_tile, "moves": game.moves, "merges": game.merges},
        )
        applied = self.core.finalize_game(result)
        game.reward_applied = applied
        if applied:
            self.save_state()
        return applied

    def handle_signal_serpent(self, action):
        game = self.signal_serpent
        if action in ("up", "down", "left", "right"):
            game.set_direction(action)
        elif action in ("select", "pause"):
            if game.game_over:
                self.finalize_signal_serpent()
                game.new_game()
            else:
                game.paused = not game.paused
                self.show_toast("PAUSED" if game.paused else "RESUMED")
        elif action == "restart":
            self.finalize_signal_serpent()
            game.new_game()

    def finalize_signal_serpent(self):
        game = self.signal_serpent
        if game.reward_applied or (game.score <= 0 and game.length <= 3):
            return False
        result = GameResult(
            reward_id=f"game:signal_serpent:{game.run_id}",
            game_id="signal_serpent",
            score=game.score,
            metrics={
                "length": game.length,
                "best_combo": game.best_combo,
                "shards": game.shards_collected,
                "speed_tier": game.speed_tier,
            },
        )
        applied = self.core.finalize_game(result)
        game.reward_applied = applied
        if applied:
            self.save_state()
        return applied

    def handle_blackglass(self, action):
        game = self.blackglass
        if action in ("up", "down", "left", "right"):
            dr, dc = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}[action]
            game.cursor = ((game.cursor[0] + dr) % 8, (game.cursor[1] + dc) % 8)
        elif action == "select":
            if game.game_over:
                self.finalize_blackglass()
                game.new_game()
                return
            options = game.moves_from(game.selected) if game.selected else []
            move = next((candidate for candidate in options if candidate.end == game.cursor), None)
            if move:
                game.play(move)
                game.cpu_turn()
            elif game.moves_from(game.cursor):
                game.selected = game.cursor
            else:
                game.selected = None
        elif action == "x":
            game.mode = "LOCAL" if game.mode == "CPU" else "CPU"
            game.new_game()
            self.show_toast(f"MODE // {game.mode}")
        elif action == "y":
            levels = ("EASY", "NORMAL", "HARD")
            game.difficulty = levels[(levels.index(game.difficulty) + 1) % len(levels)]
            self.show_toast(f"CPU // {game.difficulty}")
        elif action in ("pause",):
            game.paused = not game.paused
        elif action == "restart":
            self.finalize_blackglass()
            game.new_game()
        if game.game_over:
            self.finalize_blackglass()

    def finalize_blackglass(self):
        game = self.blackglass
        if game.reward_applied or not game.game_over:
            return False
        if game.mode == "LOCAL":
            self.game_stats["blackglass_local_matches"] += 1
            game.reward_applied = True
            self.core_profile.add_activity("game", "Blackglass local match complete — no ecosystem reward")
            self.save_state()
            return True
        won = game.winner == "black"
        score = game.captures["black"] * 40 + game.kings_created["black"] * 30 + (250 if won else 0)
        result = GameResult(f"game:blackglass:{game.run_id}", "blackglass", score, {
            "won": int(won), "normal_win": int(won and game.difficulty in ("NORMAL", "HARD")),
            "king_safe_win": int(won and game.kings_lost["black"] == 0), "captures": game.captures["black"],
            "kings": game.kings_created["black"], "difficulty": game.difficulty,
        })
        applied = self.core.finalize_game(result)
        game.reward_applied = applied
        if applied:
            self.behavior.react("CELEBRATING" if won else "WORRIED")
            self.save_state()
        return applied

    def all_quests(self):
        return self.core_profile.quests + self.core_profile.weekly_quests

    def handle_list_navigation(self, action, count, *, home=False):
        attribute = "selected_index" if home else "module_index"
        value = getattr(self, attribute)
        if action == "up":
            setattr(self, attribute, (value - 1) % count)
        elif action == "down":
            setattr(self, attribute, (value + 1) % count)
        elif action == "select" and home:
            self.open_page(MENU_ITEMS[value])

    def open_page(self, page, *, push=True):
        if push and page != self.page:
            self.page_stack.append(self.page)
        self.page = page
        self.module_index = 0
        self.transition = 1.0
        self.toast_timer = 0.0

    def perform_care_action(self, action):
        old_level = self.voidling.level
        old_bond = self.voidling.bond
        result = self.voidling.perform_action(
            action,
            self.current_relic(),
            reward_pool=EXPLORE_REWARDS,
        )
        message = result.message
        if result.reward_item_id:
            message = f"FOUND {ITEMS[result.reward_item_id].name} // +{result.xp_gained} XP"
        elif result.success:
            message += f" // +{result.xp_gained} XP"
        self.show_toast(message)
        if result.success:
            self.core_profile.add_activity("care", f"{action.title()} with Nyx")
            self.core_profile.profile_stats["care_actions"] += 1
            self.core.record_event("care_action", 1)
            if action == "EXPLORE":
                self.core_profile.profile_stats["explores"] += 1
                self.core.record_event("explore", 1)
            self.core.record_event("xp_gained", result.xp_gained)
            if result.reward_item_id:
                discover(self.core_profile, "materials" if result.reward_item_id in ("void_shard", "prism_seed") else "items", result.reward_item_id)
                self.notifications.push("ITEM FOUND", ITEMS[result.reward_item_id].name)
                self.core_profile.add_activity("item", f"Found {ITEMS[result.reward_item_id].name}")
            self.core.track_voidling_milestones(old_level, old_bond)
            self.behavior.react("EXCITED" if result.reward_item_id else "HAPPY")
            self.save_state()

    def inventory_ids(self):
        return [item_id for item_id in ITEMS if self.voidling.inventory.get(item_id, 0) > 0]

    def use_selected_item(self):
        item_id = self.inventory_ids()[self.module_index]
        old_level = self.voidling.level
        old_bond = self.voidling.bond
        result = self.voidling.use_item(ITEMS[item_id], self.current_relic())
        self.show_toast(result.message + (f" // +{result.xp_gained} XP" if result.success else ""))
        self.module_index = min(self.module_index, max(0, len(self.inventory_ids()) - 1))
        if result.success:
            self.core_profile.add_activity("item", f"Used {ITEMS[item_id].name}")
            self.core.record_event("item_used", 1)
            self.core.record_event("xp_gained", result.xp_gained)
            self.core.track_voidling_milestones(old_level, old_bond)
            self.save_state()

    def toggle_setting(self, label):
        self.settings[label] = not self.settings[label]
        if label == "SIM CHARGER":
            self.hardware.set_charging(self.settings[label])
        self.show_toast(f"{label} // {'ON' if self.settings[label] else 'OFF'}")
        self.save_state()

    def show_toast(self, message):
        self.toast = message
        self.toast_timer = 2.5

    @staticmethod
    def action_for_event(event):
        if event.type == pygame.QUIT:
            return "quit"
        if event.type != pygame.KEYDOWN:
            return None
        action = keyboard_action(event.key, pygame)
        return action.value if action else None

    def update(self, dt):
        self.transition = max(0.0, self.transition - dt * 4.5)
        self.toast_timer = max(0.0, self.toast_timer - dt)
        self.notifications.update(dt)
        if self.notifications.active:
            token = (self.notifications.active.title, self.notifications.active.message)
            if token != self._notification_token and self.settings.get("SOUND"):
                self.audio.play("important" if self.notifications.active.priority in ("IMPORTANT", "SYSTEM") else "notification")
            self._notification_token = token
        else:
            self._notification_token = None
        self.hardware.update(dt)
        if self.page == "SIGNAL SERPENT":
            was_over = self.signal_serpent.game_over
            self.signal_serpent.update(dt)
            if self.signal_serpent.game_over and not was_over:
                self.finalize_signal_serpent()
        self.profile_tick += dt
        self.autosave_tick += dt
        self.quest_tick += dt
        if self.profile_tick >= 5.0:
            self.voidling.apply_elapsed_time(self.profile_tick, self.current_relic())
            self.profile_tick = 0.0
        if self.quest_tick >= 60.0:
            if self.core.refresh_quests():
                self.notifications.push("QUEST RESET", "NEW OBJECTIVES AVAILABLE", "SYSTEM")
                self.core_profile.add_activity("quests", "Daily objectives refreshed")
                self.save_state()
            self.quest_tick = 0.0
        battery = self.hardware.snapshot().battery_percent
        if battery <= 10 and not self.low_battery_notified:
            self.notifications.push("BATTERY LOW", f"{battery:.1f}% REMAINING", "SYSTEM")
            self.low_battery_notified = True
        elif battery > 12:
            self.low_battery_notified = False
        if self.autosave_tick >= 30.0:
            self.save_state()
            self.autosave_tick = 0.0
        self.core_profile.profile_stats["playtime_seconds"] += dt

    def draw(self):
        elapsed = time.monotonic() - self.started_at
        self.surface.fill(BLACK)
        if self.show_splash and elapsed < self.splash_duration:
            self.draw_splash(elapsed / self.splash_duration)
        else:
            self.draw_console(elapsed)
        pygame.transform.smoothscale(self.surface, self.window.get_size(), self.window)
        pygame.display.flip()

    def draw_splash(self, progress):
        glow = int(105 + 55 * math.sin(progress * math.pi))
        draw_text(self.surface, self.fonts["title"], "VOID", (600, 378), (195, glow, 255), center=True)
        draw_text(self.surface, self.fonts["small"], "LIVING SYSTEM // BUILD 0.3", (600, 446), MUTED, center=True)
        bar = pygame.Rect(420, 493, 360, 8)
        pygame.draw.rect(self.surface, (29, 26, 38), bar)
        pygame.draw.rect(self.surface, PURPLE, (bar.x, bar.y, int(bar.width * progress), bar.height))
        draw_text(self.surface, self.fonts["tiny"], f"SYNC {int(progress * 100):02d}%", (600, 526), PURPLE_LIGHT, center=True)

    def draw_console(self, elapsed):
        self.draw_body()
        top = self.surface.subsurface(TOP_SCREEN)
        bottom = self.surface.subsurface(BOTTOM_SCREEN)
        top.fill(SCREEN)
        bottom.fill(SCREEN)

        if self.page == "HOME":
            self.draw_home(top)
        elif self.page == "VOIDLING":
            self.draw_voidling_hub(top, elapsed)
        elif self.page in VOIDLING_SECTIONS:
            self.draw_voidling_module(top)
        elif self.page == "VOID MERGE 2048":
            self.draw_void_merge(top)
        elif self.page == "SIGNAL SERPENT":
            self.draw_signal_serpent(top)
        elif self.page == "BLACKGLASS CHECKERS":
            self.draw_blackglass(top)
        elif self.page == "QUESTS":
            self.draw_quests(top)
        elif self.page == "MARKET":
            self.draw_market(top)
        else:
            self.draw_system_module(top)
        self.draw_bottom_context(bottom, elapsed)
        self.draw_controls()

        if self.settings["SCANLINES"]:
            self.draw_scanlines(top)
            self.draw_scanlines(bottom, spacing=5, alpha=10)
        if self.transition > 0:
            veil = pygame.Surface(TOP_SCREEN.size, pygame.SRCALPHA)
            veil.fill((153, 86, 255, int(self.transition * 58)))
            top.blit(veil, (0, 0))
        self.draw_notification(top)

    def draw_body(self):
        pygame.draw.rect(self.surface, BODY, TOP_BODY, border_radius=26)
        pygame.draw.rect(self.surface, BODY_EDGE, TOP_BODY, 2, border_radius=26)
        pygame.draw.rect(self.surface, BODY, BOTTOM_BODY, border_radius=28)
        pygame.draw.rect(self.surface, BODY_EDGE, BOTTOM_BODY, 2, border_radius=28)
        hinge = pygame.Rect(166, 501, 868, 34)
        pygame.draw.rect(self.surface, (9, 10, 14), hinge)
        pygame.draw.line(self.surface, PURPLE_DARK, (205, 518), (995, 518), 2)
        for x in (205, 995):
            pygame.draw.circle(self.surface, BODY_EDGE, (x, 518), 6, 2)
        pygame.draw.rect(self.surface, (2, 3, 6), TOP_SCREEN.inflate(12, 12), border_radius=4)
        pygame.draw.rect(self.surface, PURPLE_DARK, TOP_SCREEN.inflate(12, 12), 2, border_radius=4)
        pygame.draw.rect(self.surface, (2, 3, 6), BOTTOM_SCREEN.inflate(12, 12), border_radius=4)
        pygame.draw.rect(self.surface, BODY_EDGE, BOTTOM_SCREEN.inflate(12, 12), 2, border_radius=4)
        pygame.draw.circle(self.surface, PURPLE_DARK, (600, 58), 3)
        draw_text(self.surface, self.fonts["tiny"], "VOID // FLIP 03", (485, 836), MUTED)

    def draw_header(self, screen, section, title, right_text="SYSTEM READY"):
        draw_text(screen, self.fonts["tiny"], f"VOID SHELL  /  {section}", (28, 18), PURPLE_LIGHT)
        draw_text(screen, self.fonts["heading"], title, (28, 39))
        right_width = self.fonts["tiny"].size(right_text)[0]
        right_x = screen.get_width() - 28 - right_width
        draw_text(screen, self.fonts["tiny"], right_text, (right_x, 24), GREEN)
        pygame.draw.circle(screen, GREEN, (right_x - 14, 31), 3)
        pygame.draw.line(screen, BODY_EDGE, (28, 78), (screen.get_width() - 28, 78), 1)

    def draw_home(self, screen):
        snapshot = self.hardware.snapshot()
        power_state = "CHARGING" if snapshot.charging else "BATTERY"
        self.draw_header(screen, "CORE LOOP", "VOID // HOME", f"{power_state} {snapshot.battery_percent:04.1f}%")

        summary = pygame.Rect(28, 90, 260, 111)
        draw_panel(screen, summary)
        draw_text(screen, self.fonts["tiny"], "PLAYER SIGNAL", (45, 104), PURPLE_LIGHT)
        self.draw_status_row(screen, "NYX", f"LV {self.voidling.level} // {self.voidling.mood}", 45, 126, width=225)
        self.draw_status_row(screen, "BOND", str(self.voidling.bond), 45, 145, width=225)
        self.draw_status_row(screen, "FLUX", f"{self.core_profile.flux}", 45, 164, width=225)
        self.draw_status_row(screen, "NODE", "OFFLINE", 45, 183, width=225)

        today_panel = pygame.Rect(305, 90, 527, 111)
        draw_panel(screen, today_panel)
        draw_text(screen, self.fonts["tiny"], "TODAY + WEEKLY OBJECTIVES", (322, 104), PURPLE_LIGHT)
        visible_quests = self.core_profile.quests[:2] + self.core_profile.weekly_quests[:1]
        for row, quest in enumerate(visible_quests):
            state = "DONE" if quest.get("claimed") else f"{quest.get('progress', 0)}/{quest.get('target', 1)}"
            color = GREEN if quest.get("claimed") else WHITE
            draw_text(screen, self.fonts["tiny"], fit_text(self.fonts["tiny"], quest.get("title", "QUEST"), 270), (322, 129 + row * 22), color)
            value_width = self.fonts["tiny"].size(state)[0]
            draw_text(screen, self.fonts["tiny"], state, (811 - value_width, 129 + row * 22), color)

        recent_panel = pygame.Rect(28, 213, 360, 111)
        draw_panel(screen, recent_panel)
        draw_text(screen, self.fonts["tiny"], "LIVING SIGNAL", (45, 227), PURPLE_LIGHT)
        thought = self.behavior.current_thought(self.voidling, "HOME")
        latest_note = self.notifications.history[-1] if self.notifications.history else {"title": "SYSTEM", "message": "Living System ready"}
        recent = [{"message": f"NYX: {thought}"}, {"message": f"{latest_note['title']}: {latest_note['message']}"}] + list(reversed(self.core_profile.activity[-1:]))
        for row, event in enumerate(recent):
            draw_text(screen, self.fonts["tiny"], fit_text(self.fonts["tiny"], event.get("message", ""), 320), (45, 254 + row * 22), MUTED if row else WHITE)

        for index, label in enumerate(MENU_ITEMS):
            column = index % 3
            row = index // 3
            x = 407 + column * 143
            y = 213 + row * 37
            selected = index == self.selected_index
            lock_id = {"MARKET": "market", "WORKSHOP": "workshop"}.get(label)
            locked = bool(lock_id and not is_unlocked(lock_id, self.voidling.level))
            rect = pygame.Rect(x, y, 135, 33)
            pygame.draw.rect(screen, PURPLE_DARK if selected else PANEL, rect)
            pygame.draw.rect(screen, PURPLE if selected else BODY_EDGE, rect, 1)
            text = f"{label} {'LOCK' if locked else ''}".strip()
            draw_text(screen, self.fonts["tiny"], fit_text(self.fonts["tiny"], text, 115), rect.center, WHITE if selected else MUTED, center=True)
        self.draw_footer(screen, "D-PAD  NAVIGATE", "X/Y/TAB  QUICK PLAY", "Q  POWER")

    def draw_voidling_hub(self, screen, elapsed):
        relic = self.current_relic()
        self.draw_header(screen, "VOIDLING", self.voidling.name.upper(), f"{self.voidling.mood} // LV {self.voidling.level:02d}")
        portrait = pygame.Rect(28, 96, 270, 222)
        draw_panel(screen, portrait)
        self.draw_voidling_sprite(screen, (163, 180), elapsed, scale=1.35)
        draw_text(screen, self.fonts["tiny"], f"BOND {self.voidling.bond:03d}", (54, 286), PURPLE_LIGHT)
        draw_text(screen, self.fonts["tiny"], relic.name if relic else "NO RELIC", (164, 286), GREEN if relic else MUTED)

        self.draw_stat_block(screen, 320, 100, "ENERGY", self.voidling.energy / self.voidling.energy_cap(relic), f"{self.voidling.energy:.0f}", GREEN)
        self.draw_stat_block(screen, 320, 140, "FULLNESS", self.voidling.fullness / 100, f"{self.voidling.fullness:.0f}", PURPLE)
        self.draw_stat_block(screen, 320, 180, "JOY", self.voidling.joy / 100, f"{self.voidling.joy:.0f}", PURPLE_LIGHT)
        self.draw_stat_block(screen, 320, 220, "HEALTH", self.voidling.health / 100, f"{self.voidling.health:.0f}", GREEN)
        self.draw_stat_block(screen, 320, 260, "LEVEL XP", self.voidling.xp_progress, f"{self.voidling.xp}/{self.voidling.xp_to_next_level}", PURPLE)

        for index, label in enumerate(VOIDLING_SECTIONS):
            y = 96 + index * 46
            selected = index == self.module_index
            rect = pygame.Rect(600, y, 232, 37)
            pygame.draw.rect(screen, PURPLE_DARK if selected else PANEL, rect)
            pygame.draw.rect(screen, PURPLE if selected else BODY_EDGE, rect, 1)
            draw_text(screen, self.fonts["small"], label, (620, y + 7), WHITE if selected else MUTED)
        self.draw_footer(screen, "UP/DOWN  SELECT", "ENTER  OPEN", "ESC  HOME")

    def draw_stat_block(self, screen, x, y, label, progress, value, color):
        draw_text(screen, self.fonts["tiny"], label, (x, y), MUTED)
        value_width = self.fonts["tiny"].size(value)[0]
        draw_text(screen, self.fonts["tiny"], value, (570 - value_width, y), WHITE)
        draw_meter(screen, pygame.Rect(x, y + 19, 250, 10), progress, color)

    def draw_voidling_module(self, screen):
        titles = {"CARE": "CARE ROUTINES", "INVENTORY": "PACK INVENTORY", "RELICS": "RELIC MATRIX", "WORKSHOP": "RELIC WORKSHOP",
                  "MASTERY": "GAME MASTERY", "CHALLENGES": "CHALLENGE MATRIX", "CODEX": "VOID CODEX", "PROFILE": "LOCAL PROFILE",
                  "JOURNAL": "VOIDLING JOURNAL", "NOTIFICATIONS": "NOTIFICATION CENTER"}
        right = {"CARE": self.behavior.state(self.voidling), "INVENTORY": f"{sum(self.voidling.inventory.values())} ITEMS",
                 "RELICS": f"{len(self.voidling.owned_relics)} OWNED", "WORKSHOP": "MATERIAL CRAFTING",
                 "MASTERY": "THREE SIGNALS", "CHALLENGES": f"{len(self.core_profile.completed_challenges)} COMPLETE",
                 "CODEX": "DISCOVERY LOG", "PROFILE": self.core_profile.display_name, "JOURNAL": f"BOND {self.voidling.bond}",
                 "NOTIFICATIONS": f"{len(self.notifications.history)} STORED"}
        self.draw_header(screen, f"VOIDLING / {self.page}", titles[self.page], right[self.page])
        rows = self.voidling_rows()
        self.draw_scrolling_rows(screen, rows, visible=5)
        action = "ENTER  USE" if self.page == "INVENTORY" else "ENTER  ACT"
        if self.page == "RELICS":
            action = "ENTER  EQUIP"
        if self.page == "WORKSHOP":
            action = "ENTER  CRAFT"
        if self.page == "JOURNAL":
            action = "PROGRESS RECORD"
        if self.page in ("MASTERY", "CHALLENGES", "CODEX", "PROFILE", "NOTIFICATIONS"):
            action = "INSPECT"
        self.draw_footer(screen, "UP/DOWN  SELECT", action, "ESC  VOIDLING")
        if self.toast_timer > 0:
            self.draw_toast(screen)

    def voidling_rows(self):
        if self.page == "CARE":
            return CARE_ACTIONS
        if self.page == "INVENTORY":
            return tuple((ITEMS[item_id].name, f"x{self.voidling.inventory[item_id]}", ITEMS[item_id].rarity) for item_id in self.inventory_ids()) or (("PACK EMPTY", "--", "--"),)
        if self.page == "RELICS":
            rows = []
            for relic_id in self.voidling.owned_relics:
                relic = RELICS[relic_id]
                state = "EQUIPPED" if relic_id == self.voidling.equipped_relic else relic.rarity
                rows.append((relic.name, relic.slot, state))
            return tuple(rows) or (("NO RELICS", "--", "--"),)
        if self.page == "WORKSHOP":
            rows = []
            for recipe in RELIC_RECIPES:
                relic = RELICS[recipe.relic_id]
                advanced_locked = recipe != RELIC_RECIPES[0] and not is_unlocked("advanced_relics", self.voidling.level)
                state = "OWNED" if relic.relic_id in self.voidling.owned_relics else f"LOCKED LV {UNLOCK_LEVELS['advanced_relics']}" if advanced_locked else relic.rarity
                cost = " / ".join(f"{item_id.split('_')[0].upper()} x{quantity}" for item_id, quantity in recipe.ingredients.items())
                rows.append((relic.name, cost, state))
            return tuple(rows)
        if self.page == "MASTERY":
            return tuple((GAME_TITLES[game_id], f"LEVEL {level_for_xp(data.get('xp', 0))}", f"{data.get('xp', 0) % 100}/100 XP")
                         for game_id, data in self.core_profile.mastery.items())
        if self.page == "CHALLENGES":
            return tuple((challenge.title, GAME_TITLES[challenge.game_id], "COMPLETE" if challenge.challenge_id in self.core_profile.completed_challenges else "LOCKED")
                         for challenge in CHALLENGES)
        if self.page == "CODEX":
            rows = []
            for item_id, item in ITEMS.items():
                category = "materials" if item_id in ("void_shard", "prism_seed") else "items"
                found = item_id in self.core_profile.codex.get(category, [])
                owned = self.voidling.inventory.get(item_id, 0) > 0
                rows.append((item.name if found else "??? ITEM", category.upper(), "OWNED" if owned else "DISCOVERED" if found else "UNDISCOVERED"))
            for relic_id, relic in RELICS.items():
                found = relic_id in self.core_profile.codex.get("relics", [])
                rows.append((relic.name if found else "??? RELIC", "RELICS", "OWNED" if relic_id in self.voidling.owned_relics else "DISCOVERED" if found else "UNDISCOVERED"))
            for game_id, title in GAME_TITLES.items():
                found = game_id in self.core_profile.codex.get("games", [])
                rows.append((title if found else "??? SIGNAL", "GAMES", "DISCOVERED" if found else "UNDISCOVERED"))
            for achievement in ACHIEVEMENTS:
                found = achievement.achievement_id in self.core_profile.completed_achievements
                rows.append((achievement.title if found else "??? ACHIEVEMENT", achievement.category.upper(), "DISCOVERED" if found else "UNDISCOVERED"))
            for badge in self.core_profile.codex.get("mastery_badges", []):
                rows.append((badge.replace(":", " M").replace("_", " ").upper(), "MASTERY BADGES", "OWNED"))
            return tuple(rows)
        if self.page == "PROFILE":
            played = {game_id: data.get("games_played", 0) for game_id, data in self.core_profile.mastery.items()}
            favorite = GAME_TITLES.get(max(played, key=played.get), "NONE") if played and max(played.values()) else "NONE"
            totals = {"items": 5, "materials": 2, "relics": len(RELICS), "games": 3, "achievements": len(ACHIEVEMENTS), "mastery_badges": 15}
            return (("DISPLAY NAME", self.core_profile.display_name, "LOCAL ONLY"), ("NYX", f"LEVEL {self.voidling.level}", f"BOND {self.voidling.bond}"),
                    ("FLUX", str(self.core_profile.flux), "IN-DEVICE"), ("GAMES PLAYED", str(sum(played.values())), favorite),
                    ("ACHIEVEMENTS", f"{len(self.core_profile.completed_achievements)}/{len(ACHIEVEMENTS)}", "COMPLETE"),
                    ("CODEX", f"{completion(self.core_profile, totals) * 100:.0f}%", "DISCOVERED"),
                    ("STREAK", f"{self.core_profile.current_streak} DAYS", f"BEST {self.core_profile.longest_streak}"),
                    ("TOP MASTERY", str(max((level_for_xp(data.get('xp', 0)) for data in self.core_profile.mastery.values()), default=1)), "LEVEL"),
                    ("PLAYTIME", f"{self.core_profile.profile_stats.get('playtime_seconds', 0) / 3600:.1f}H", "LOCAL"))
        if self.page == "NOTIFICATIONS":
            return tuple((note.get("title", "NOTICE"), note.get("message", ""), note.get("priority", "INFO"))
                         for note in reversed(self.notifications.history)) or (("NO NOTIFICATIONS", "SYSTEM QUIET", "INFO"),)
        achievements = tuple((entry.title, entry.category.upper(), "COMPLETE" if entry.achievement_id in self.core_profile.completed_achievements else "LOCKED") for entry in ACHIEVEMENTS)
        activity_rows = tuple(
            (event.get("message", "EVENT"), event.get("time", "").split("T")[-1], "EVENT")
            for event in reversed(self.core_profile.activity[-8:])
        )
        return achievements + activity_rows

    def draw_system_module(self, screen):
        title_map = {"GAMES": "GAME ROADMAP", "EMULATORS": "EMULATOR BAY", "FRIENDS": "FRIEND LINK", "TRADING": "TRADE TERMINAL", "SETTINGS": "SYSTEM SETTINGS"}
        right_map = {"GAMES": "VOIDLING FIRST", "EMULATORS": "LEGAL SETUP", "FRIENDS": "LOCAL ONLY", "TRADING": "SAFE MODE", "SETTINGS": "LIVE CONFIG"}
        self.draw_header(screen, self.page, title_map[self.page], right_map[self.page])
        if self.page == "GAMES":
            rows = []
            for game in GAME_LIBRARY:
                state = game.status
                if game.game_id == "signal_serpent" and not is_unlocked("signal_serpent", self.voidling.level):
                    state = f"LOCKED LV {UNLOCK_LEVELS['signal_serpent']}"
                rows.append((game.title, game.genre, state))
            rows = tuple(rows)
        elif self.page == "EMULATORS":
            rows = EMULATOR_SYSTEMS
        elif self.page == "FRIENDS":
            rows = FRIEND_SLOTS
        elif self.page == "TRADING":
            rows = tuple((ITEMS[item_id].name, f"x{self.voidling.inventory.get(item_id, 0)}", ITEMS[item_id].rarity) for item_id in ITEMS if self.voidling.inventory.get(item_id, 0))
        else:
            rows = tuple((label, "OPTION", "ON" if self.settings[label] else "OFF") for label in SETTING_LABELS)
        self.draw_scrolling_rows(screen, rows, visible=4)
        middle = "ENTER  DETAILS"
        if self.page == "SETTINGS":
            middle = "ENTER/LEFT/RIGHT  TOGGLE"
        self.draw_footer(screen, "UP/DOWN  SELECT", middle, "ESC  HOME")
        if self.toast_timer > 0:
            self.draw_toast(screen)

    def draw_quests(self, screen):
        quests = self.all_quests()
        completed = sum(1 for quest in quests if quest.get("claimed"))
        self.draw_header(screen, "CORE / QUESTS", "DAILY + WEEKLY", f"{completed}/{len(quests)} COMPLETE")
        rows = []
        for quest in quests:
            progress = f"{quest.get('progress', 0)}/{quest.get('target', 1)}"
            state = "CLAIMED" if quest.get("claimed") else progress
            rows.append((quest.get("title", "QUEST"), quest.get("description", ""), state))
        self.draw_scrolling_rows(screen, tuple(rows), visible=4)
        draw_text(screen, self.fonts["tiny"], "REWARDS AUTO-CLAIM WHEN AN OBJECTIVE COMPLETES", (430, 319), MUTED, center=True)
        self.draw_footer(screen, "UP/DOWN  INSPECT", "AUTO-CLAIM ENABLED", "ESC  HOME")

    def draw_market(self, screen):
        unlocked = is_unlocked("market", self.voidling.level)
        right = f"FLUX {self.core_profile.flux}" if unlocked else f"LOCKED // LV {UNLOCK_LEVELS['market']}"
        self.draw_header(screen, "CORE / MARKET", "VOID MARKET", right)
        rows = tuple((entry.title, f"{entry.price} FLUX", "BUY" if unlocked else "LOCKED") for entry in MARKET_STOCK)
        self.draw_scrolling_rows(screen, rows, visible=5)
        self.draw_footer(screen, "UP/DOWN  SELECT", "ENTER  PURCHASE", "ESC  HOME")
        if self.toast_timer > 0:
            self.draw_toast(screen)

    def draw_blackglass(self, screen):
        game = self.blackglass
        self.draw_header(screen, "GAMES / BOARD", "BLACKGLASS CHECKERS", f"{game.mode} // {game.difficulty}")
        size, origin_x, origin_y = 36, 46, 88
        moves = legal_moves(game.board, game.turn)
        destinations = {move.end for move in moves if move.start == game.selected}
        for row in range(8):
            for col in range(8):
                rect = pygame.Rect(origin_x + col * size, origin_y + row * size, size, size)
                pygame.draw.rect(screen, (27, 23, 38) if (row + col) % 2 else (10, 11, 16), rect)
                if (row, col) == game.cursor:
                    pygame.draw.rect(screen, GREEN, rect, 2)
                if (row, col) == game.selected:
                    pygame.draw.rect(screen, PURPLE_LIGHT, rect, 3)
                if (row, col) in destinations:
                    pygame.draw.circle(screen, GREEN, rect.center, 5)
                piece = game.board[row][col]
                if piece != ".":
                    color = PURPLE if piece.lower() == "b" else (190, 196, 214)
                    pygame.draw.circle(screen, color, rect.center, 13)
                    pygame.draw.circle(screen, WHITE if piece.isupper() else BODY_EDGE, rect.center, 13, 2)
                    if piece.isupper():
                        draw_text(screen, self.fonts["tiny"], "K", rect.center, SCREEN, center=True)
        draw_panel(screen, pygame.Rect(375, 88, 457, 288))
        state = "GAME OVER" if game.game_over else "PAUSED" if game.paused else f"{game.turn.upper()} TURN"
        rows = (("STATE", state), ("BLACK CAPTURES", str(game.captures["black"])), ("WHITE CAPTURES", str(game.captures["white"])),
                ("LEGAL MOVES", str(len(moves))), ("MODE", game.mode), ("CPU", game.difficulty))
        for index, (label, value) in enumerate(rows):
            self.draw_status_row(screen, label, value, 401, 112 + index * 34, width=400)
        footer = f"WINNER // {game.winner.upper()}" if game.winner else "A SELECT // X MODE // Y CPU // R RESTART"
        draw_text(screen, self.fonts["tiny"], footer, (603, 338), PURPLE_LIGHT, center=True)

    def draw_signal_serpent(self, screen):
        game = self.signal_serpent
        high = max(self.game_stats["signal_serpent_high_score"], game.score)
        self.draw_header(screen, "GAMES / SERPENT", "SIGNAL SERPENT", f"HIGH {high:05d}")
        cell = 20
        board_x, board_y = 36, 96
        board = pygame.Rect(board_x - 5, board_y - 5, game.width * cell + 10, game.height * cell + 10)
        pygame.draw.rect(screen, PANEL, board)
        pygame.draw.rect(screen, PURPLE_DARK, board, 2)
        for x, y in game.corruption:
            rect = pygame.Rect(board_x + x * cell + 3, board_y + y * cell + 3, cell - 6, cell - 6)
            pygame.draw.rect(screen, (91, 25, 74), rect)
            pygame.draw.line(screen, PURPLE_LIGHT, rect.topleft, rect.bottomright, 1)
        if game.signal:
            x, y = game.signal
            pygame.draw.circle(screen, PURPLE_LIGHT, (board_x + x * cell + 10, board_y + y * cell + 10), 6)
        if game.shard:
            x, y = game.shard
            points = [(board_x + x * cell + 10, board_y + y * cell + 2), (board_x + x * cell + 17, board_y + y * cell + 10), (board_x + x * cell + 10, board_y + y * cell + 18), (board_x + x * cell + 3, board_y + y * cell + 10)]
            pygame.draw.polygon(screen, GREEN, points)
        for index, (x, y) in enumerate(reversed(game.snake)):
            rect = pygame.Rect(board_x + x * cell + 2, board_y + y * cell + 2, cell - 4, cell - 4)
            color = GREEN if index == len(game.snake) - 1 else PURPLE
            pygame.draw.rect(screen, color, rect, border_radius=4)

        panel = pygame.Rect(430, 91, 402, 274)
        draw_panel(screen, panel)
        draw_text(screen, self.fonts["tiny"], "LIVE SIGNAL", (451, 110), PURPLE_LIGHT)
        telemetry = (
            ("SCORE", f"{game.score:05d}"),
            ("LENGTH", str(game.length)),
            ("COMBO", f"x{game.combo}"),
            ("SPEED", f"TIER {game.speed_tier}"),
            ("SHARDS", str(game.shards_collected)),
            ("REWARD", reward_tier("signal_serpent", game.score)),
        )
        for row, (label, value) in enumerate(telemetry):
            self.draw_status_row(screen, label, value, 451, 143 + row * 26)
        state = "COLLISION // ENTER RESTART" if game.game_over else "PAUSED" if game.paused else "SIGNAL LIVE"
        draw_text(screen, self.fonts["small"], state, (631, 316), PURPLE_LIGHT if game.game_over else GREEN, center=True)
        draw_text(screen, self.fonts["tiny"], "D-PAD MOVE // ENTER PAUSE // R RESTART", (631, 344), MUTED, center=True)
        if self.toast_timer > 0:
            self.draw_toast(screen)

    def draw_notification(self, screen):
        notification = self.notifications.active
        if not notification:
            return
        age = notification.duration - notification.remaining
        slide = 0
        if age < 0.22:
            slide = int((1 - age / 0.22) * 350)
        elif notification.remaining < 0.35:
            slide = int((1 - notification.remaining / 0.35) * 350)
        rect = pygame.Rect(screen.get_width() - 350 + slide, 84, 322, 57)
        pygame.draw.rect(screen, (20, 13, 31), rect)
        pygame.draw.rect(screen, PURPLE, rect, 1)
        accent = {"INFO": PURPLE_LIGHT, "REWARD": GREEN, "IMPORTANT": (255, 196, 92), "SYSTEM": (109, 191, 255)}.get(notification.priority, GREEN)
        pygame.draw.rect(screen, accent, (rect.x, rect.y, 4, rect.height))
        draw_text(screen, self.fonts["tiny"], f"{notification.priority} // {notification.title}", (rect.x + 18, rect.y + 10), accent)
        draw_text(screen, self.fonts["tiny"], fit_text(self.fonts["tiny"], notification.message, 286), (rect.x + 18, rect.y + 32), WHITE)

    def draw_void_merge(self, screen):
        game = self.void_merge
        self.draw_header(screen, "GAMES / VOID MERGE", "VOID MERGE 2048", f"HIGH {self.game_stats['void_merge_high_score']:06d}")
        palette = {
            0: (19, 18, 28), 2: (44, 33, 61), 4: (58, 38, 80), 8: (77, 43, 112),
            16: (95, 48, 140), 32: (117, 55, 169), 64: (142, 65, 199),
            128: (99, 76, 196), 256: (73, 105, 205), 512: (53, 139, 194),
            1024: (55, 176, 163), 2048: (82, 218, 166),
        }
        origin_x, origin_y, tile, gap = 46, 93, 62, 8
        board_rect = pygame.Rect(origin_x - 8, origin_y - 8, tile * 4 + gap * 5, tile * 4 + gap * 5)
        pygame.draw.rect(screen, PANEL, board_rect)
        pygame.draw.rect(screen, PURPLE_DARK, board_rect, 2)
        for row in range(4):
            for column in range(4):
                value = game.board[row][column]
                rect = pygame.Rect(origin_x + column * (tile + gap), origin_y + row * (tile + gap), tile, tile)
                color = palette.get(value, (95, 226, 176))
                pygame.draw.rect(screen, color, rect, border_radius=4)
                pygame.draw.rect(screen, BODY_EDGE, rect, 1, border_radius=4)
                if value:
                    font = self.fonts["body"] if value < 1000 else self.fonts["small"]
                    draw_text(screen, font, str(value), rect.center, WHITE, center=True)

        draw_panel(screen, pygame.Rect(365, 93, 467, 270))
        draw_text(screen, self.fonts["tiny"], "RUN TELEMETRY", (389, 112), PURPLE_LIGHT)
        telemetry = (
            ("SCORE", f"{game.score:06d}"),
            ("LAST MERGE", f"+{game.last_gain}"),
            ("MOVES", str(game.moves)),
            ("HIGHEST CORE", str(game.highest_tile)),
            ("TARGET", str(game.target)),
        )
        for row, (label, value) in enumerate(telemetry):
            self.draw_status_row(screen, label, value, 389, 145 + row * 29)
        state = "GRID LOCKED" if game.game_over else "CORE STABLE"
        if game.won:
            state = "2048 CORE FORMED"
        if game.paused:
            state = "PAUSED"
        draw_text(screen, self.fonts["small"], state, (600, 308), GREEN if not game.game_over else PURPLE_LIGHT, center=True)
        draw_text(screen, self.fonts["tiny"], "ARROWS MOVE  //  ENTER PAUSE  //  R RESTART", (600, 337), MUTED, center=True)
        if self.toast_timer > 0:
            self.draw_toast(screen)

    def draw_scrolling_rows(self, screen, rows, visible=4):
        if not rows:
            rows = (("NO ENTRIES", "--", "--"),)
        start = max(0, min(self.module_index - visible + 1, len(rows) - visible))
        start = max(0, start)
        for slot, row in enumerate(rows[start:start + visible]):
            index = start + slot
            y = 94 + slot * (49 if visible == 5 else 59)
            selected = index == self.module_index
            rect = pygame.Rect(28, y, 804, 40 if visible == 5 else 49)
            pygame.draw.rect(screen, PURPLE_DARK if selected else PANEL, rect)
            pygame.draw.rect(screen, PURPLE if selected else BODY_EDGE, rect, 1)
            if selected:
                pygame.draw.rect(screen, PURPLE_LIGHT, (28, y, 4, rect.height))
            draw_text(screen, self.fonts["small"], fit_text(self.fonts["small"], row[0], 390), (48, y + 5), WHITE if selected else MUTED)
            draw_text(screen, self.fonts["tiny"], fit_text(self.fonts["tiny"], row[1], 175), (470, y + 12), WHITE if selected else MUTED)
            state_color = GREEN if str(row[2]) in ("ONLINE", "ON", "COMPLETE", "EQUIPPED", "ADAPTER READY", "PLAYABLE") else PURPLE_LIGHT
            draw_text(screen, self.fonts["tiny"], fit_text(self.fonts["tiny"], row[2], 150), (665, y + 12), state_color if selected else MUTED)
        if len(rows) > visible:
            draw_text(screen, self.fonts["tiny"], f"{self.module_index + 1:02d}/{len(rows):02d}", (786, 318), MUTED)

    def draw_status_row(self, screen, label, value, x, y, *, width=244):
        draw_text(screen, self.fonts["tiny"], label, (x, y), MUTED)
        value_width = self.fonts["tiny"].size(value)[0]
        draw_text(screen, self.fonts["tiny"], value, (x + width - value_width, y), WHITE)

    def draw_footer(self, screen, left, middle, right):
        pygame.draw.line(screen, BODY_EDGE, (28, 342), (screen.get_width() - 28, 342), 1)
        draw_text(screen, self.fonts["tiny"], left, (28, 355), MUTED)
        draw_text(screen, self.fonts["tiny"], middle, (screen.get_width() // 2, 355), PURPLE_LIGHT, center=True)
        right_width = self.fonts["tiny"].size(right)[0]
        draw_text(screen, self.fonts["tiny"], right, (screen.get_width() - 28 - right_width, 355), MUTED)

    def draw_toast(self, screen):
        width = min(650, self.fonts["tiny"].size(self.toast)[0] + 42)
        rect = pygame.Rect((screen.get_width() - width) // 2, 311, width, 28)
        pygame.draw.rect(screen, (31, 20, 48), rect)
        pygame.draw.rect(screen, PURPLE, rect, 1)
        draw_text(screen, self.fonts["tiny"], self.toast, rect.center, PURPLE_LIGHT, center=True)

    def draw_bottom_context(self, screen, elapsed):
        if self.page in VOIDLING_SECTIONS:
            self.draw_selected_context(screen)
        elif self.page == "VOID MERGE 2048":
            self.draw_void_merge_context(screen)
        elif self.page == "SIGNAL SERPENT":
            self.draw_signal_serpent_context(screen)
        elif self.page == "BLACKGLASS CHECKERS":
            self.draw_blackglass_context(screen)
        elif self.page == "GAMES":
            self.draw_game_menu_context(screen)
        elif self.page == "MARKET":
            self.draw_market_context(screen)
        elif self.page == "QUESTS":
            self.draw_quest_context(screen)
        elif self.page == "SETTINGS":
            self.draw_settings_context(screen)
        else:
            self.draw_companion_summary(screen, elapsed)

    def draw_void_merge_context(self, screen):
        game = self.void_merge
        draw_text(screen, self.fonts["tiny"], "VOID MERGE // OBJECTIVE", (18, 14), PURPLE_LIGHT)
        pygame.draw.line(screen, BODY_EDGE, (18, 36), (372, 36), 1)
        draw_panel(screen, pygame.Rect(18, 53, 354, 164))
        draw_text(screen, self.fonts["heading"], str(game.highest_tile), (195, 91), GREEN, center=True)
        draw_text(screen, self.fonts["tiny"], "HIGHEST CORE", (195, 122), MUTED, center=True)
        remaining = max(0, game.target - game.highest_tile)
        draw_meter(screen, pygame.Rect(47, 151, 296, 12), min(1, game.highest_tile / game.target), GREEN)
        tier = reward_tier("void_merge", game.score)
        draw_text(screen, self.fonts["tiny"], f"{remaining} REMAINING // {tier} REWARD", (195, 184), PURPLE_LIGHT, center=True)
        reaction = "NYX: THE GRID IS SINGING." if game.score >= 1500 else "NYX: KEEP BUILDING THE CORE."
        draw_text(screen, self.fonts["tiny"], reaction, (195, 205), MUTED, center=True)

    def draw_signal_serpent_context(self, screen):
        game = self.signal_serpent
        draw_text(screen, self.fonts["tiny"], "SIGNAL SERPENT // REWARD LINK", (18, 14), PURPLE_LIGHT)
        pygame.draw.line(screen, BODY_EDGE, (18, 36), (372, 36), 1)
        draw_panel(screen, pygame.Rect(18, 53, 354, 164))
        draw_text(screen, self.fonts["heading"], f"x{game.combo}", (195, 82), GREEN, center=True)
        draw_text(screen, self.fonts["tiny"], "CURRENT COMBO", (195, 111), MUTED, center=True)
        rows = (("LENGTH", str(game.length)), ("SPEED", f"TIER {game.speed_tier}"), ("ESTIMATE", reward_tier("signal_serpent", game.score)))
        for row, (label, value) in enumerate(rows):
            self.draw_status_row(screen, label, value, 47, 139 + row * 23)

    def draw_blackglass_context(self, screen):
        game = self.blackglass
        draw_text(screen, self.fonts["tiny"], "BLACKGLASS // NYX ANALYSIS", (18, 14), PURPLE_LIGHT)
        pygame.draw.line(screen, BODY_EDGE, (18, 36), (372, 36), 1)
        draw_panel(screen, pygame.Rect(18, 53, 354, 164))
        advantage = game.captures["black"] - game.captures["white"]
        draw_text(screen, self.fonts["heading"], f"{game.turn.upper()} TURN", (195, 79), GREEN, center=True)
        rows = (("CAPTURE BALANCE", f"{advantage:+d}"), ("BLACK KINGS", str(game.kings_created["black"])),
                ("MATCH", game.mode), ("NYX", "THINK TWO MOVES AHEAD" if not game.game_over else "GOOD MATCH"))
        for row, (label, value) in enumerate(rows):
            self.draw_status_row(screen, label, value, 38, 120 + row * 22, width=314)

    def draw_game_menu_context(self, screen):
        game = GAME_LIBRARY[self.module_index]
        draw_text(screen, self.fonts["tiny"], "GAMES // SELECTED", (18, 14), PURPLE_LIGHT)
        pygame.draw.line(screen, BODY_EDGE, (18, 36), (372, 36), 1)
        draw_panel(screen, pygame.Rect(18, 53, 354, 164))
        draw_text(screen, self.fonts["small"], fit_text(self.fonts["small"], game.title, 310), (38, 70), WHITE)
        draw_text(screen, self.fonts["tiny"], game.genre, (38, 101), PURPLE_LIGHT)
        draw_text(screen, self.fonts["tiny"], fit_text(self.fonts["tiny"], game.description, 310), (38, 129), MUTED)
        if game.game_id == "merge_2048":
            stats = f"HIGH {self.game_stats['void_merge_high_score']} // RUNS {self.game_stats['void_merge_runs']}"
        elif game.game_id == "signal_serpent":
            stats = f"HIGH {self.game_stats['signal_serpent_high_score']} // RUNS {self.game_stats['signal_serpent_total_runs']}"
        elif game.game_id == "blackglass":
            stats = f"WINS {self.game_stats['blackglass_wins']} // LOCAL {self.game_stats['blackglass_local_matches']}"
        else:
            stats = "ROADMAP ONLY // NO FAKE LAUNCH"
        if game.game_id in self.core_profile.mastery:
            stats += f" // M{level_for_xp(self.core_profile.mastery[game.game_id].get('xp', 0))}"
        draw_text(screen, self.fonts["tiny"], stats, (38, 176), GREEN if game.playable else MUTED)
        rewards = "REWARDS // XP + FLUX + MATERIALS" if game.playable else "STATUS // DESIGN QUEUE"
        draw_text(screen, self.fonts["tiny"], rewards, (38, 199), PURPLE_LIGHT if game.playable else MUTED)

    def draw_market_context(self, screen):
        entry = MARKET_STOCK[self.module_index]
        unlocked = is_unlocked("market", self.voidling.level)
        can_buy = unlocked and self.core_profile.flux >= entry.price
        draw_text(screen, self.fonts["tiny"], "VOID MARKET // ITEM", (18, 14), PURPLE_LIGHT)
        pygame.draw.line(screen, BODY_EDGE, (18, 36), (372, 36), 1)
        draw_panel(screen, pygame.Rect(18, 53, 354, 164))
        draw_text(screen, self.fonts["small"], entry.title, (38, 70), WHITE)
        draw_text(screen, self.fonts["tiny"], fit_text(self.fonts["tiny"], entry.description, 310), (38, 103), MUTED)
        draw_text(screen, self.fonts["heading"], f"{entry.price} FLUX", (195, 151), PURPLE_LIGHT, center=True)
        state = "ENTER TO BUY" if can_buy else "INSUFFICIENT FLUX" if unlocked else f"UNLOCKS LEVEL {UNLOCK_LEVELS['market']}"
        draw_text(screen, self.fonts["tiny"], f"BALANCE {self.core_profile.flux} // {state}", (195, 192), GREEN if can_buy else MUTED, center=True)

    def draw_quest_context(self, screen):
        quest = self.all_quests()[self.module_index]
        weekly = self.module_index >= len(self.core_profile.quests)
        definition = WEEKLY_BY_ID[quest["id"]] if weekly else QUESTS_BY_ID[quest["id"]]
        draw_text(screen, self.fonts["tiny"], f"{'WEEKLY' if weekly else 'DAILY'} SIGNAL // DETAIL", (18, 14), PURPLE_LIGHT)
        pygame.draw.line(screen, BODY_EDGE, (18, 36), (372, 36), 1)
        draw_panel(screen, pygame.Rect(18, 53, 354, 164))
        draw_text(screen, self.fonts["small"], quest["title"], (38, 70), WHITE)
        draw_text(screen, self.fonts["tiny"], fit_text(self.fonts["tiny"], quest["description"], 310), (38, 101), MUTED)
        progress = min(1, quest.get("progress", 0) / max(1, quest.get("target", 1)))
        draw_meter(screen, pygame.Rect(38, 133, 314, 11), progress, GREEN)
        draw_text(screen, self.fonts["tiny"], fit_text(self.fonts["tiny"], definition.reward.summary(), 310), (38, 163), PURPLE_LIGHT)
        state = "CLAIMED" if quest.get("claimed") else f"{quest.get('progress', 0)} / {quest.get('target', 1)}"
        draw_text(screen, self.fonts["tiny"], state, (38, 191), GREEN if quest.get("claimed") else WHITE)

    def draw_companion_summary(self, screen, elapsed):
        draw_text(screen, self.fonts["tiny"], f"VOIDLING // {self.page} CONTEXT", (18, 14), PURPLE_LIGHT)
        pygame.draw.line(screen, BODY_EDGE, (18, 36), (372, 36), 1)
        self.draw_voidling_sprite(screen, (91, 113), elapsed)
        draw_text(screen, self.fonts["body"], self.voidling.name.upper(), (162, 50))
        state = self.behavior.state(self.voidling)
        draw_text(screen, self.fonts["tiny"], f"LV {self.voidling.level:02d} // {state}", (163, 80), MUTED)
        stats = (("EN", self.voidling.energy / self.voidling.energy_cap(self.current_relic()), GREEN), ("FULL", self.voidling.fullness / 100, PURPLE), ("JOY", self.voidling.joy / 100, PURPLE_LIGHT))
        for row, (label, progress, color) in enumerate(stats):
            y = 107 + row * 27
            draw_text(screen, self.fonts["tiny"], label, (163, y), MUTED)
            draw_meter(screen, pygame.Rect(210, y + 1, 150, 11), progress, color)
        relic = self.current_relic()
        draw_text(screen, self.fonts["tiny"], f"BOND {self.voidling.bond} // {relic.name if relic else 'NO RELIC'}", (163, 194), WHITE)
        status = self.behavior.current_thought(self.voidling, self.page)
        draw_text(screen, self.fonts["tiny"], fit_text(self.fonts["tiny"], status, 210), (163, 216), PURPLE_LIGHT)

    def draw_voidling_sprite(self, screen, center, elapsed, scale=1.0):
        state = self.behavior.state(self.voidling)
        speed = 4.7 if state in ("EXCITED", "CELEBRATING") else 1.4 if state == "SLEEPING" else 2.3
        amplitude = 7 if state in ("EXCITED", "CELEBRATING") else 2 if state in ("TIRED", "SLEEPING") else 4
        bob = int(math.sin(elapsed * speed) * amplitude) if self.settings["ANIMATIONS"] else 0
        cx, cy = center[0], center[1] + bob
        w, h = int(42 * scale), int(52 * scale)
        pygame.draw.ellipse(screen, (30, 18, 48), (cx - int(50 * scale), cy + int(53 * scale), int(100 * scale), int(14 * scale)))
        outer = [(cx, cy - h), (cx + w, cy - 18), (cx + 32, cy + 37), (cx, cy + 51), (cx - 32, cy + 37), (cx - w, cy - 18)]
        inner = [(cx, cy - int(42 * scale)), (cx + int(31 * scale), cy - 13), (cx + 23, cy + 29), (cx, cy + 40), (cx - 23, cy + 29), (cx - int(31 * scale), cy - 13)]
        pygame.draw.polygon(screen, PURPLE_DARK, outer)
        pygame.draw.polygon(screen, PURPLE, inner, 2)
        blink = self.settings["ANIMATIONS"] and int(elapsed * 2) % 13 == 0
        if blink or state == "SLEEPING":
            pygame.draw.line(screen, PURPLE_LIGHT, (cx - 17, cy - 4), (cx - 9, cy - 4), 2)
            pygame.draw.line(screen, PURPLE_LIGHT, (cx + 9, cy - 4), (cx + 17, cy - 4), 2)
        else:
            look = int(math.sin(elapsed * .7) * 2)
            pygame.draw.circle(screen, PURPLE_LIGHT, (cx - 13 + look, cy - 4), max(3, int(4 * scale)))
            pygame.draw.circle(screen, PURPLE_LIGHT, (cx + 13 + look, cy - 4), max(3, int(4 * scale)))
        if state in ("HAPPY", "EXCITED", "PROUD", "CELEBRATING"):
            pygame.draw.arc(screen, PURPLE_LIGHT, (cx - 10, cy + 1, 20, 14), math.pi, math.pi * 2, 2)
        else:
            pygame.draw.arc(screen, PURPLE_LIGHT, (cx - 10, cy + 5, 20, 12), 0.15, math.pi - 0.15, 2)

    def draw_selected_context(self, screen):
        draw_text(screen, self.fonts["tiny"], f"{self.page} // DETAIL", (18, 14), PURPLE_LIGHT)
        pygame.draw.line(screen, BODY_EDGE, (18, 36), (372, 36), 1)
        draw_panel(screen, pygame.Rect(18, 53, 354, 164))
        if self.page == "CARE":
            name, effect, description = CARE_ACTIONS[self.module_index]
            lines = (name, effect, description, "Actions change needs, bond, and XP.")
        elif self.page == "INVENTORY" and self.inventory_ids():
            item = ITEMS[self.inventory_ids()[self.module_index]]
            lines = (item.name, f"{item.rarity} // {item.category}", item.description, "ENTER TO USE" if item.usable else "CRAFTING MATERIAL")
        elif self.page == "RELICS" and self.voidling.owned_relics:
            relic = RELICS[self.voidling.owned_relics[self.module_index]]
            lines = (relic.name, f"{relic.rarity} // {relic.slot}", relic.description, "ENTER TO EQUIP / REMOVE")
        elif self.page == "WORKSHOP":
            recipe = RELIC_RECIPES[self.module_index]
            relic = RELICS[recipe.relic_id]
            cost = " + ".join(f"{ITEMS[item_id].name} x{quantity}" for item_id, quantity in recipe.ingredients.items())
            advanced_locked = self.module_index > 0 and not is_unlocked("advanced_relics", self.voidling.level)
            ready = not advanced_locked and all(self.voidling.inventory.get(item_id, 0) >= quantity for item_id, quantity in recipe.ingredients.items())
            status = f"LOCKED LEVEL {UNLOCK_LEVELS['advanced_relics']}" if advanced_locked else "READY" if ready else "NEED MATERIALS"
            lines = (relic.name, f"{relic.rarity} // {relic.slot}", relic.description, f"{status} // {cost}")
        else:
            rows = self.voidling_rows()
            lines = (rows[self.module_index][0], rows[self.module_index][1], rows[self.module_index][2], f"TOTAL ACTIONS {self.voidling.total_actions}")
        draw_text(screen, self.fonts["body"], lines[0], (38, 70), WHITE)
        draw_text(screen, self.fonts["tiny"], lines[1], (38, 101), PURPLE_LIGHT)
        draw_text(screen, self.fonts["tiny"], fit_text(self.fonts["tiny"], lines[2], 310), (38, 130), MUTED)
        draw_text(screen, self.fonts["tiny"], fit_text(self.fonts["tiny"], lines[3], 310), (38, 181), GREEN)

    def draw_settings_context(self, screen):
        label = SETTING_LABELS[self.module_index]
        descriptions = {
            "SCANLINES": "Subtle display texture.",
            "ANIMATIONS": "Lightweight companion motion.",
            "SOUND": "Procedural UI and game feedback.",
            "STATUS DETAIL": "Expanded device telemetry.",
            "SIM CHARGER": "Desktop-only charging source.",
        }
        draw_text(screen, self.fonts["tiny"], "SETTINGS // LIVE PREVIEW", (18, 14), PURPLE_LIGHT)
        pygame.draw.line(screen, BODY_EDGE, (18, 36), (372, 36), 1)
        draw_panel(screen, pygame.Rect(18, 55, 354, 172))
        draw_text(screen, self.fonts["small"], label, (38, 74), WHITE)
        draw_text(screen, self.fonts["tiny"], descriptions[label], (38, 109), MUTED)
        state = "ENABLED" if self.settings[label] else "DISABLED"
        draw_text(screen, self.fonts["heading"], state, (195, 151), GREEN if self.settings[label] else PURPLE_LIGHT, center=True)
        snapshot = self.hardware.snapshot()
        draw_text(screen, self.fonts["tiny"], f"{snapshot.battery_percent:.1f}% // {'CHARGING' if snapshot.charging else 'BATTERY'}", (195, 176), MUTED, center=True)
        draw_text(screen, self.fonts["tiny"], "NODE OFFLINE // NETWORK LOCAL", (195, 197), MUTED, center=True)
        save_path = str(self.store.path) if self.store else "PERSISTENCE DISABLED"
        draw_text(screen, self.fonts["tiny"], fit_text(self.fonts["tiny"], save_path, 320), (195, 216), MUTED, center=True)

    @staticmethod
    def draw_scanlines(screen, spacing=4, alpha=13):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        for y in range(0, screen.get_height(), spacing):
            pygame.draw.line(overlay, (0, 0, 0, alpha), (0, y), (screen.get_width(), y))
        screen.blit(overlay, (0, 0))

    def draw_controls(self):
        pygame.draw.rect(self.surface, PANEL_LIGHT, (205, 635, 52, 154), border_radius=7)
        pygame.draw.rect(self.surface, PANEL_LIGHT, (154, 686, 154, 52), border_radius=7)
        pygame.draw.rect(self.surface, BODY_EDGE, (205, 635, 52, 154), 2, border_radius=7)
        pygame.draw.rect(self.surface, BODY_EDGE, (154, 686, 154, 52), 2, border_radius=7)
        pygame.draw.circle(self.surface, (9, 10, 14), (231, 712), 14)
        pygame.draw.polygon(self.surface, MUTED, [(231, 648), (221, 662), (241, 662)])
        pygame.draw.polygon(self.surface, MUTED, [(231, 776), (221, 762), (241, 762)])
        pygame.draw.polygon(self.surface, MUTED, [(167, 712), (181, 702), (181, 722)])
        pygame.draw.polygon(self.surface, MUTED, [(295, 712), (281, 702), (281, 722)])
        positions = {"X": (969, 650), "Y": (909, 710), "A": (1029, 710), "B": (969, 770)}
        for label, center in positions.items():
            pygame.draw.circle(self.surface, PANEL_LIGHT, center, 29)
            pygame.draw.circle(self.surface, BODY_EDGE, center, 29, 2)
            color = PURPLE_LIGHT if label in ("A", "B") else MUTED
            draw_text(self.surface, self.fonts["body"], label, center, color, center=True)
        draw_text(self.surface, self.fonts["tiny"], "MOVE", (210, 810), MUTED)
        draw_text(self.surface, self.fonts["tiny"], "SELECT", (1002, 810), MUTED)

    def run(self, *, max_frames=None, screenshot: Path | None = None):
        frame_count = 0
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                action = self.action_for_event(event)
                if action:
                    self.handle_action(action)
            self.update(dt)
            self.draw()
            frame_count += 1
            if max_frames is not None and frame_count >= max_frames:
                if screenshot:
                    pygame.image.save(self.surface, str(screenshot))
                break
        self.save_state()
        pygame.quit()
