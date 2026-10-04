"""Void Flip shell, companion simulation, navigation, and rendering."""

from __future__ import annotations

import math
import time
from pathlib import Path

import pygame

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
from games.void_merge import VoidMergeGame
from models import Voidling
from persistence import ProfileStore
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
MENU_ITEMS = ("VOIDLING", "GAMES", "EMULATORS", "FRIENDS", "TRADING", "SETTINGS")
VOIDLING_SECTIONS = ("CARE", "INVENTORY", "RELICS", "WORKSHOP", "JOURNAL")
PAGE_PARENTS = {
    "VOIDLING": "HOME",
    "CARE": "VOIDLING",
    "INVENTORY": "VOIDLING",
    "RELICS": "VOIDLING",
    "WORKSHOP": "VOIDLING",
    "JOURNAL": "VOIDLING",
    "GAMES": "HOME",
    "EMULATORS": "HOME",
    "FRIENDS": "HOME",
    "TRADING": "HOME",
    "SETTINGS": "HOME",
    "VOID MERGE 2048": "GAMES",
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

    def __init__(self, *, show_splash=True, persist=True, save_path=None):
        pygame.init()
        pygame.display.set_caption("Void Flip v0.2.1")
        self.surface = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.fonts = make_fonts()
        self.running = True
        self.page = "HOME"
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

        self.store = ProfileStore(save_path) if persist else None
        payload = self.store.load() if self.store else {}
        self.settings = {
            "SCANLINES": True,
            "ANIMATIONS": True,
            "STATUS DETAIL": True,
            "SIM CHARGER": False,
        }
        self.settings.update({key: bool(value) for key, value in payload.get("settings", {}).items() if key in self.settings})
        self.voidling = Voidling.from_dict(payload.get("voidling", {})) if payload.get("voidling") else Voidling()
        self.game_stats = {"void_merge_high_score": 0}
        self.game_stats.update(payload.get("game_stats", {}))
        self.void_merge = VoidMergeGame()
        self.hardware = DesktopHardwareAdapter(
            battery_percent=float(payload.get("battery_percent", 86.0)),
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
        snapshot = self.hardware.snapshot()
        self.store.save({
            "voidling": self.voidling.to_dict(),
            "settings": self.settings,
            "battery_percent": round(snapshot.battery_percent, 3),
            "game_stats": self.game_stats,
        })

    def handle_action(self, action):
        """Update state independently of keyboard, GPIO, or touch sources."""

        if action == "quit":
            self.save_state()
            self.running = False
            return
        if action == "back":
            self.open_page(PAGE_PARENTS.get(self.page, "HOME"))
            return

        if self.page == "HOME":
            self.handle_list_navigation(action, len(MENU_ITEMS), home=True)
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
                self.save_state()
        elif self.page == "WORKSHOP":
            self.handle_list_navigation(action, len(RELIC_RECIPES))
            if action == "select":
                recipe = RELIC_RECIPES[self.module_index]
                result = self.voidling.craft_relic(recipe, RELICS[recipe.relic_id])
                message = result.message + (f" // +{result.xp_gained} XP" if result.success else "")
                self.show_toast(message)
                if result.success:
                    self.save_state()
        elif self.page == "JOURNAL":
            self.handle_list_navigation(action, 4)
        elif self.page == "GAMES":
            self.handle_list_navigation(action, len(GAME_LIBRARY))
            if action == "select":
                game = GAME_LIBRARY[self.module_index]
                if game.game_id == "merge_2048" and game.playable:
                    self.open_page("VOID MERGE 2048")
                else:
                    self.show_toast(f"{game.title} // DEVELOPMENT QUEUE")
        elif self.page == "VOID MERGE 2048":
            self.handle_void_merge(action)
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

    def handle_void_merge(self, action):
        if action in ("up", "down", "left", "right"):
            if self.void_merge.move(action):
                high_score = max(self.game_stats["void_merge_high_score"], self.void_merge.score)
                self.game_stats["void_merge_high_score"] = high_score
                self.save_state()
            elif self.void_merge.game_over:
                self.show_toast("GRID LOCKED // ENTER TO RESTART")
        elif action == "select":
            if self.void_merge.game_over:
                self.void_merge.new_game()
                self.show_toast("NEW GRID INITIALIZED")
            else:
                self.void_merge.paused = not self.void_merge.paused
                self.show_toast("PAUSED" if self.void_merge.paused else "RESUMED")
        elif action == "restart":
            self.void_merge.new_game()
            self.show_toast("GRID RESTARTED")
        elif action == "pause":
            self.void_merge.paused = not self.void_merge.paused

    def handle_list_navigation(self, action, count, *, home=False):
        attribute = "selected_index" if home else "module_index"
        value = getattr(self, attribute)
        if action == "up":
            setattr(self, attribute, (value - 1) % count)
        elif action == "down":
            setattr(self, attribute, (value + 1) % count)
        elif action == "select" and home:
            self.open_page(MENU_ITEMS[value])

    def open_page(self, page):
        self.page = page
        self.module_index = 0
        self.transition = 1.0
        self.toast_timer = 0.0

    def perform_care_action(self, action):
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
            self.save_state()

    def inventory_ids(self):
        return [item_id for item_id in ITEMS if self.voidling.inventory.get(item_id, 0) > 0]

    def use_selected_item(self):
        item_id = self.inventory_ids()[self.module_index]
        result = self.voidling.use_item(ITEMS[item_id], self.current_relic())
        self.show_toast(result.message + (f" // +{result.xp_gained} XP" if result.success else ""))
        self.module_index = min(self.module_index, max(0, len(self.inventory_ids()) - 1))
        if result.success:
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
        key_actions = {
            pygame.K_q: "quit",
            pygame.K_UP: "up", pygame.K_w: "up",
            pygame.K_DOWN: "down", pygame.K_s: "down",
            pygame.K_LEFT: "left", pygame.K_a: "left",
            pygame.K_RIGHT: "right", pygame.K_d: "right",
            pygame.K_RETURN: "select", pygame.K_SPACE: "select",
            pygame.K_ESCAPE: "back", pygame.K_BACKSPACE: "back",
            pygame.K_r: "restart", pygame.K_p: "pause",
        }
        return key_actions.get(event.key)

    def update(self, dt):
        self.transition = max(0.0, self.transition - dt * 4.5)
        self.toast_timer = max(0.0, self.toast_timer - dt)
        self.hardware.update(dt)
        self.profile_tick += dt
        self.autosave_tick += dt
        if self.profile_tick >= 5.0:
            self.voidling.apply_elapsed_time(self.profile_tick, self.current_relic())
            self.profile_tick = 0.0
        if self.autosave_tick >= 30.0:
            self.save_state()
            self.autosave_tick = 0.0

    def draw(self):
        elapsed = time.monotonic() - self.started_at
        self.surface.fill(BLACK)
        if self.show_splash and elapsed < self.splash_duration:
            self.draw_splash(elapsed / self.splash_duration)
        else:
            self.draw_console(elapsed)
        pygame.display.flip()

    def draw_splash(self, progress):
        glow = int(105 + 55 * math.sin(progress * math.pi))
        draw_text(self.surface, self.fonts["title"], "VOID", (600, 378), (195, glow, 255), center=True)
        draw_text(self.surface, self.fonts["small"], "COMPANION CORE // BUILD 0.2.1", (600, 446), MUTED, center=True)
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
        elif self.page in ("CARE", "INVENTORY", "RELICS", "WORKSHOP", "JOURNAL"):
            self.draw_voidling_module(top)
        elif self.page == "VOID MERGE 2048":
            self.draw_void_merge(top)
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
        draw_text(self.surface, self.fonts["tiny"], "VOID // FLIP 02", (485, 836), MUTED)

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
        self.draw_header(screen, "LOCAL", "HOME", f"{power_state} {snapshot.battery_percent:04.1f}%")
        descriptions = (
            "CARE + CRAFT",
            "1 PLAYABLE",
            "3 ADAPTERS",
            "LOCAL LINK",
            f"{sum(self.voidling.inventory.values())} ITEMS",
            "4 OPTIONS",
        )
        for index, label in enumerate(MENU_ITEMS):
            y = 91 + index * 39
            selected = index == self.selected_index
            rect = pygame.Rect(28, y, 500, 32)
            if selected:
                pygame.draw.rect(screen, PURPLE_DARK, rect)
                pygame.draw.rect(screen, PURPLE, rect, 1)
                pygame.draw.polygon(screen, PURPLE_LIGHT, [(41, y + 9), (49, y + 16), (41, y + 23)])
            draw_text(screen, self.fonts["tiny"], f"0{index + 1}", (61, y + 9), PURPLE_LIGHT if selected else MUTED)
            draw_text(screen, self.fonts["small"], label, (102, y + 5), WHITE if selected else MUTED)
            draw_text(screen, self.fonts["tiny"], descriptions[index], (390, y + 9), WHITE if selected else MUTED)

        panel = pygame.Rect(552, 91, 280, 234)
        draw_panel(screen, panel)
        draw_text(screen, self.fonts["tiny"], "DEVICE PULSE", (570, 108), PURPLE_LIGHT)
        rows = (
            ("VOIDLING", f"{self.voidling.mood} L{self.voidling.level}"),
            ("NETWORK", snapshot.network),
            ("TEMP", f"{snapshot.temperature_c:.1f} C"),
            ("POWER", power_state),
            ("BUILD", "0.2.1"),
        )
        if not self.settings["STATUS DETAIL"]:
            rows = (("VOIDLING", self.voidling.mood), ("POWER", f"{snapshot.battery_percent:.0f}%"), ("BUILD", "0.2.1"))
        for row, (label, value) in enumerate(rows):
            self.draw_status_row(screen, label, value, 570, 140 + row * 29)
        draw_meter(screen, pygame.Rect(570, 296, 244, 10), snapshot.battery_percent / 100, GREEN)
        self.draw_footer(screen, "UP/DOWN  NAVIGATE", "ENTER  OPEN", "Q  POWER")

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
        titles = {"CARE": "CARE ROUTINES", "INVENTORY": "PACK INVENTORY", "RELICS": "RELIC MATRIX", "WORKSHOP": "RELIC WORKSHOP", "JOURNAL": "VOIDLING JOURNAL"}
        right = {"CARE": self.voidling.mood, "INVENTORY": f"{sum(self.voidling.inventory.values())} ITEMS", "RELICS": f"{len(self.voidling.owned_relics)} OWNED", "WORKSHOP": "MATERIAL CRAFTING", "JOURNAL": f"BOND {self.voidling.bond}"}
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
                state = "OWNED" if relic.relic_id in self.voidling.owned_relics else relic.rarity
                cost = " / ".join(f"{item_id.split('_')[0].upper()} x{quantity}" for item_id, quantity in recipe.ingredients.items())
                rows.append((relic.name, cost, state))
            return tuple(rows)
        achievements = (
            ("FIRST BOND", "COMPLETE" if self.voidling.total_actions >= 1 else "LOCKED", "CARE ONCE"),
            ("FIELD WALKER", "COMPLETE" if self.voidling.total_actions >= 10 else "LOCKED", "10 ACTIONS"),
            ("RELIC KEEPER", "COMPLETE" if len(self.voidling.owned_relics) >= 3 else "LOCKED", "3 RELICS"),
            ("TRUE COMPANION", "COMPLETE" if self.voidling.bond >= 50 else "LOCKED", "BOND 50"),
        )
        return achievements

    def draw_system_module(self, screen):
        title_map = {"GAMES": "GAME ROADMAP", "EMULATORS": "EMULATOR BAY", "FRIENDS": "FRIEND LINK", "TRADING": "TRADE TERMINAL", "SETTINGS": "SYSTEM SETTINGS"}
        right_map = {"GAMES": "VOIDLING FIRST", "EMULATORS": "LEGAL SETUP", "FRIENDS": "LOCAL ONLY", "TRADING": "SAFE MODE", "SETTINGS": "LIVE CONFIG"}
        self.draw_header(screen, self.page, title_map[self.page], right_map[self.page])
        if self.page == "GAMES":
            rows = tuple((game.title, game.genre, game.status) for game in GAME_LIBRARY)
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

    def draw_status_row(self, screen, label, value, x, y):
        draw_text(screen, self.fonts["tiny"], label, (x, y), MUTED)
        value_width = self.fonts["tiny"].size(value)[0]
        draw_text(screen, self.fonts["tiny"], value, (x + 244 - value_width, y), WHITE)

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
        if self.page in ("CARE", "INVENTORY", "RELICS", "WORKSHOP", "JOURNAL"):
            self.draw_selected_context(screen)
        elif self.page == "VOID MERGE 2048":
            self.draw_void_merge_context(screen)
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
        draw_text(screen, self.fonts["tiny"], f"{remaining} SIGNAL MASS REMAINING", (195, 184), PURPLE_LIGHT, center=True)

    def draw_companion_summary(self, screen, elapsed):
        draw_text(screen, self.fonts["tiny"], f"VOIDLING // {self.page} CONTEXT", (18, 14), PURPLE_LIGHT)
        pygame.draw.line(screen, BODY_EDGE, (18, 36), (372, 36), 1)
        self.draw_voidling_sprite(screen, (91, 113), elapsed)
        draw_text(screen, self.fonts["body"], self.voidling.name.upper(), (162, 50))
        draw_text(screen, self.fonts["tiny"], f"LV {self.voidling.level:02d} // {self.voidling.mood}", (163, 80), MUTED)
        stats = (("EN", self.voidling.energy / self.voidling.energy_cap(self.current_relic()), GREEN), ("FULL", self.voidling.fullness / 100, PURPLE), ("JOY", self.voidling.joy / 100, PURPLE_LIGHT))
        for row, (label, progress, color) in enumerate(stats):
            y = 107 + row * 27
            draw_text(screen, self.fonts["tiny"], label, (163, y), MUTED)
            draw_meter(screen, pygame.Rect(210, y + 1, 150, 11), progress, color)
        relic = self.current_relic()
        draw_text(screen, self.fonts["tiny"], "RELIC", (163, 194), MUTED)
        draw_text(screen, self.fonts["tiny"], relic.name if relic else "NONE", (220, 194), WHITE)

    def draw_voidling_sprite(self, screen, center, elapsed, scale=1.0):
        bob = int(math.sin(elapsed * 2.3) * 4) if self.settings["ANIMATIONS"] else 0
        cx, cy = center[0], center[1] + bob
        w, h = int(42 * scale), int(52 * scale)
        pygame.draw.ellipse(screen, (30, 18, 48), (cx - int(50 * scale), cy + int(53 * scale), int(100 * scale), int(14 * scale)))
        outer = [(cx, cy - h), (cx + w, cy - 18), (cx + 32, cy + 37), (cx, cy + 51), (cx - 32, cy + 37), (cx - w, cy - 18)]
        inner = [(cx, cy - int(42 * scale)), (cx + int(31 * scale), cy - 13), (cx + 23, cy + 29), (cx, cy + 40), (cx - 23, cy + 29), (cx - int(31 * scale), cy - 13)]
        pygame.draw.polygon(screen, PURPLE_DARK, outer)
        pygame.draw.polygon(screen, PURPLE, inner, 2)
        pygame.draw.circle(screen, PURPLE_LIGHT, (cx - 13, cy - 4), max(3, int(4 * scale)))
        pygame.draw.circle(screen, PURPLE_LIGHT, (cx + 13, cy - 4), max(3, int(4 * scale)))
        pygame.draw.arc(screen, PURPLE_LIGHT, (cx - 10, cy + 1, 20, 14), 0.15, math.pi - 0.15, 2)

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
            lines = (relic.name, f"{relic.rarity} // {relic.slot}", relic.description, cost)
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
            "STATUS DETAIL": "Expanded device telemetry.",
            "SIM CHARGER": "Desktop-only charging source.",
        }
        draw_text(screen, self.fonts["tiny"], "SETTINGS // LIVE PREVIEW", (18, 14), PURPLE_LIGHT)
        pygame.draw.line(screen, BODY_EDGE, (18, 36), (372, 36), 1)
        draw_panel(screen, pygame.Rect(18, 55, 354, 151))
        draw_text(screen, self.fonts["small"], label, (38, 74), WHITE)
        draw_text(screen, self.fonts["tiny"], descriptions[label], (38, 109), MUTED)
        state = "ENABLED" if self.settings[label] else "DISABLED"
        draw_text(screen, self.fonts["heading"], state, (195, 155), GREEN if self.settings[label] else PURPLE_LIGHT, center=True)
        draw_text(screen, self.fonts["tiny"], "ENTER TO TOGGLE", (195, 188), MUTED, center=True)

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
