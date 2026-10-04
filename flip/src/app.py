"""Core Void Flip simulator state, input, and rendering."""

import math
import random
import time
from pathlib import Path

import pygame

from content import EMULATOR_SYSTEMS, FRIEND_SLOTS, GAME_LIBRARY, SETTING_LABELS, TRADE_ITEMS
from models import Voidling
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
MENU_ITEMS = ("GAMES", "EMULATORS", "FRIENDS", "TRADING", "SETTINGS")


class VoidFlipApp:
    """State and renderer for the hardware-agnostic Void Flip shell."""

    def __init__(self, *, show_splash=True):
        pygame.init()
        pygame.display.set_caption("Void Flip v0.2")
        self.surface = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.fonts = make_fonts()
        self.voidling = Voidling()
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
        self.settings = {
            "SCANLINES": True,
            "ANIMATIONS": True,
            "STATUS DETAIL": True,
        }

        # Signal Catch is the first real built-in game loop.
        self.game_player_x = TOP_SCREEN.width // 2
        self.game_orb_x = 230
        self.game_orb_y = 98.0
        self.game_score = 0
        self.game_misses = 0

    def handle_action(self, action):
        """Update state without depending on a particular physical input source."""

        if action == "quit":
            self.running = False
            return

        if self.page == "SIGNAL CATCH":
            if action == "back":
                self.open_page("GAMES")
            elif action == "left":
                self.game_player_x = max(80, self.game_player_x - 30)
            elif action == "right":
                self.game_player_x = min(TOP_SCREEN.width - 80, self.game_player_x + 30)
            return

        if action == "back":
            if self.page != "HOME":
                self.open_page("HOME")
            return

        if self.page == "HOME":
            if action == "up":
                self.selected_index = (self.selected_index - 1) % len(MENU_ITEMS)
            elif action == "down":
                self.selected_index = (self.selected_index + 1) % len(MENU_ITEMS)
            elif action == "select":
                self.open_page(MENU_ITEMS[self.selected_index])
            return

        row_count = self.module_row_count()
        if action == "up":
            self.module_index = (self.module_index - 1) % row_count
        elif action == "down":
            self.module_index = (self.module_index + 1) % row_count
        elif action in ("left", "right", "select"):
            self.activate_module_row()

    def open_page(self, page):
        self.page = page
        self.module_index = 0
        self.transition = 1.0
        self.toast_timer = 0.0

    def module_row_count(self):
        if self.page == "GAMES":
            return len(GAME_LIBRARY)
        if self.page == "SETTINGS":
            return len(SETTING_LABELS)
        return 3

    def activate_module_row(self):
        if self.page == "GAMES":
            game = GAME_LIBRARY[self.module_index]
            if game.playable:
                self.reset_game()
                self.open_page(game.title)
            else:
                self.show_toast(f"{game.title} // NOT INSTALLED")
        elif self.page == "SETTINGS":
            label = SETTING_LABELS[self.module_index]
            self.settings[label] = not self.settings[label]
            self.show_toast(f"{label} // {'ON' if self.settings[label] else 'OFF'}")
        elif self.page == "EMULATORS":
            self.show_toast("CONFIGURATION REQUIRED")
        elif self.page == "FRIENDS":
            self.show_toast("LOCAL DISCOVERY ACTIVE")
        elif self.page == "TRADING":
            self.show_toast("TRUSTED TRADE SERVICE REQUIRED")

    def show_toast(self, message):
        self.toast = message
        self.toast_timer = 2.2

    def reset_game(self):
        self.game_player_x = TOP_SCREEN.width // 2
        self.game_orb_x = random.randint(90, TOP_SCREEN.width - 90)
        self.game_orb_y = 102.0
        self.game_score = 0
        self.game_misses = 0

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
        }
        return key_actions.get(event.key)

    def update(self, dt):
        self.transition = max(0.0, self.transition - dt * 4.5)
        self.toast_timer = max(0.0, self.toast_timer - dt)
        if self.page == "SIGNAL CATCH":
            self.update_signal_catch(dt)

    def update_signal_catch(self, dt):
        self.game_orb_y += (112 + self.game_score * 5) * dt
        catch_y = 306
        if self.game_orb_y >= catch_y:
            if abs(self.game_orb_x - self.game_player_x) <= 62:
                self.game_score += 1
                self.show_toast("SIGNAL CAPTURED")
            else:
                self.game_misses += 1
                self.show_toast("SIGNAL LOST")
            self.game_orb_x = random.randint(90, TOP_SCREEN.width - 90)
            self.game_orb_y = 102.0

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
        draw_text(self.surface, self.fonts["small"], "FLIP SHELL // BUILD 0.2", (600, 446), MUTED, center=True)
        bar = pygame.Rect(420, 493, 360, 8)
        pygame.draw.rect(self.surface, (29, 26, 38), bar)
        pygame.draw.rect(self.surface, PURPLE, (bar.x, bar.y, int(bar.width * progress), bar.height))
        for x in range(bar.x, bar.right, 24):
            pygame.draw.line(self.surface, BLACK, (x, bar.y), (x, bar.bottom), 1)
        draw_text(self.surface, self.fonts["tiny"], f"SYNC {int(progress * 100):02d}%", (600, 526), PURPLE_LIGHT, center=True)

    def draw_console(self, elapsed):
        self.draw_body()
        top = self.surface.subsurface(TOP_SCREEN)
        bottom = self.surface.subsurface(BOTTOM_SCREEN)
        top.fill(SCREEN)
        bottom.fill(SCREEN)

        if self.page == "HOME":
            self.draw_home(top)
        elif self.page == "SIGNAL CATCH":
            self.draw_signal_catch(top)
        else:
            self.draw_module(top)
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
        # Both halves share the exact same left edge and width in v0.2.
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
        self.draw_header(screen, "LOCAL", "HOME")
        for index, label in enumerate(MENU_ITEMS):
            y = 94 + index * 47
            selected = index == self.selected_index
            rect = pygame.Rect(28, y, 500, 38)
            if selected:
                pygame.draw.rect(screen, PURPLE_DARK, rect)
                pygame.draw.rect(screen, PURPLE, rect, 1)
                pygame.draw.polygon(screen, PURPLE_LIGHT, [(41, y + 12), (49, y + 19), (41, y + 26)])
            draw_text(screen, self.fonts["tiny"], f"0{index + 1}", (61, y + 12), PURPLE_LIGHT if selected else MUTED)
            draw_text(screen, self.fonts["body"], label, (102, y + 7), WHITE if selected else MUTED)
            description = ("1 INSTALLED", "3 ADAPTERS", "LOCAL LINK", "2 ITEMS", "3 OPTIONS")[index]
            draw_text(screen, self.fonts["tiny"], description, (399, y + 12), WHITE if selected else MUTED)

        status = pygame.Rect(552, 94, 280, 225)
        draw_panel(screen, status)
        draw_text(screen, self.fonts["tiny"], "DEVICE PULSE", (570, 110), PURPLE_LIGHT)
        status_rows = (
            (("PROFILE", "NYX-01"), ("NETWORK", "LOCAL"), ("NODE", "STANDBY"), ("BATTERY", "SIM 86%"), ("BUILD", "0.2"))
            if self.settings["STATUS DETAIL"]
            else (("PROFILE", "NYX-01"), ("SYSTEM", "READY"), ("BUILD", "0.2"))
        )
        for row, (label, value) in enumerate(status_rows):
            self.draw_status_row(screen, label, value, 570, 143 + row * 29)
        draw_meter(screen, pygame.Rect(570, 291, 244, 10), 0.86, GREEN)

        self.draw_footer(screen, "UP/DOWN  NAVIGATE", "ENTER  OPEN", "Q  POWER")

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

    def draw_module(self, screen):
        title_map = {
            "GAMES": "GAME LIBRARY",
            "EMULATORS": "EMULATOR BAY",
            "FRIENDS": "FRIEND LINK",
            "TRADING": "TRADE TERMINAL",
            "SETTINGS": "SYSTEM SETTINGS",
        }
        right_map = {
            "GAMES": "1 READY",
            "EMULATORS": "3 ADAPTERS",
            "FRIENDS": "LOCAL ONLY",
            "TRADING": "SAFE MODE",
            "SETTINGS": "LIVE CONFIG",
        }
        self.draw_header(screen, self.page, title_map[self.page], right_map[self.page])

        if self.page == "GAMES":
            rows = tuple((game.title, game.genre, game.status) for game in GAME_LIBRARY)
            headings = ("TITLE", "TYPE", "STATE")
        elif self.page == "EMULATORS":
            rows = tuple((name, "ADAPTER", status) for name, status in EMULATOR_SYSTEMS)
            headings = ("SYSTEM", "MODE", "STATE")
        elif self.page == "FRIENDS":
            rows = FRIEND_SLOTS
            headings = ("LINK", "IDENTITY", "STATE")
        elif self.page == "TRADING":
            rows = TRADE_ITEMS
            headings = ("ITEM", "QTY", "CLASS")
        else:
            rows = tuple((label, "OPTION", "ON" if self.settings[label] else "OFF") for label in SETTING_LABELS)
            headings = ("SETTING", "TYPE", "VALUE")

        draw_text(screen, self.fonts["tiny"], headings[0], (48, 99), MUTED)
        draw_text(screen, self.fonts["tiny"], headings[1], (445, 99), MUTED)
        draw_text(screen, self.fonts["tiny"], headings[2], (640, 99), MUTED)
        for index, row in enumerate(rows):
            self.draw_module_row(screen, index, row)

        hint = "ENTER  LAUNCH" if self.page == "GAMES" else "ENTER  ACTION"
        if self.page == "SETTINGS":
            hint = "LEFT/RIGHT/ENTER  TOGGLE"
        self.draw_footer(screen, "UP/DOWN  SELECT", hint, "ESC  HOME")
        if self.toast_timer > 0:
            self.draw_toast(screen)

    def draw_module_row(self, screen, index, row):
        y = 121 + index * 65
        selected = index == self.module_index
        rect = pygame.Rect(28, y, 804, 52)
        pygame.draw.rect(screen, PURPLE_DARK if selected else PANEL, rect)
        pygame.draw.rect(screen, PURPLE if selected else BODY_EDGE, rect, 1)
        if selected:
            pygame.draw.rect(screen, PURPLE_LIGHT, (28, y, 4, 52))
        draw_text(screen, self.fonts["body"], row[0], (48, y + 7), WHITE if selected else MUTED)
        draw_text(screen, self.fonts["tiny"], f"ENTRY 0{index + 1}", (48, y + 32), PURPLE_LIGHT if selected else MUTED)
        draw_text(screen, self.fonts["small"], str(row[1]), (445, y + 15), WHITE if selected else MUTED)
        state_color = GREEN if row[2] in ("READY", "ONLINE", "ON", "ADAPTER READY") else PURPLE_LIGHT
        draw_text(screen, self.fonts["tiny"], str(row[2]), (640, y + 18), state_color if selected else MUTED)

    def draw_toast(self, screen):
        width = min(520, self.fonts["tiny"].size(self.toast)[0] + 42)
        rect = pygame.Rect((screen.get_width() - width) // 2, 311, width, 28)
        pygame.draw.rect(screen, (31, 20, 48), rect)
        pygame.draw.rect(screen, PURPLE, rect, 1)
        draw_text(screen, self.fonts["tiny"], self.toast, rect.center, PURPLE_LIGHT, center=True)

    def draw_signal_catch(self, screen):
        self.draw_header(screen, "GAMES / SIGNAL CATCH", "SIGNAL CATCH", f"SCORE {self.game_score:02d}")
        arena = pygame.Rect(28, 94, 804, 235)
        draw_panel(screen, arena, fill=(9, 10, 16), accent=PURPLE_DARK)
        for x in range(arena.left + 40, arena.right, 80):
            pygame.draw.line(screen, (19, 20, 30), (x, arena.top + 1), (x, arena.bottom - 1), 1)
        for y in range(arena.top + 40, arena.bottom, 40):
            pygame.draw.line(screen, (19, 20, 30), (arena.left + 1, y), (arena.right - 1, y), 1)

        pulse = 7 + int(math.sin(time.monotonic() * 7) * 2)
        pygame.draw.circle(screen, PURPLE_DARK, (int(self.game_orb_x), int(self.game_orb_y)), pulse + 7)
        pygame.draw.circle(screen, PURPLE_LIGHT, (int(self.game_orb_x), int(self.game_orb_y)), pulse)
        player = pygame.Rect(self.game_player_x - 52, 296, 104, 14)
        pygame.draw.polygon(screen, PURPLE, [(player.left, player.bottom), (player.left + 14, player.top), (player.right - 14, player.top), (player.right, player.bottom)])
        pygame.draw.line(screen, PURPLE_LIGHT, (player.left + 18, player.top), (player.right - 18, player.top), 2)
        draw_text(screen, self.fonts["tiny"], f"LOST {self.game_misses:02d}", (48, 305), MUTED)
        self.draw_footer(screen, "LEFT/RIGHT  MOVE", "CAPTURE THE SIGNAL", "ESC  LIBRARY")
        if self.toast_timer > 0:
            self.draw_toast(screen)

    def draw_bottom_context(self, screen, elapsed):
        if self.page == "SIGNAL CATCH":
            self.draw_game_context(screen)
        elif self.page == "SETTINGS":
            self.draw_settings_context(screen)
        else:
            self.draw_voidling_screen(screen, elapsed)

    def draw_voidling_screen(self, screen, elapsed):
        section = "HOME" if self.page == "HOME" else self.page
        draw_text(screen, self.fonts["tiny"], f"VOIDLING // {section} CONTEXT", (18, 14), PURPLE_LIGHT)
        pygame.draw.line(screen, BODY_EDGE, (18, 36), (372, 36), 1)

        bob = int(math.sin(elapsed * 2.3) * 4) if self.settings["ANIMATIONS"] else 0
        center = (91, 112 + bob)
        pygame.draw.ellipse(screen, (30, 18, 48), (42, 165, 100, 14))
        outer = [
            (center[0], center[1] - 52), (center[0] + 42, center[1] - 18),
            (center[0] + 32, center[1] + 37), (center[0], center[1] + 51),
            (center[0] - 32, center[1] + 37), (center[0] - 42, center[1] - 18),
        ]
        inner = [
            (center[0], center[1] - 42), (center[0] + 31, center[1] - 13),
            (center[0] + 23, center[1] + 29), (center[0], center[1] + 40),
            (center[0] - 23, center[1] + 29), (center[0] - 31, center[1] - 13),
        ]
        pygame.draw.polygon(screen, PURPLE_DARK, outer)
        pygame.draw.polygon(screen, PURPLE, inner, 2)
        pygame.draw.circle(screen, PURPLE_LIGHT, (center[0] - 13, center[1] - 4), 4)
        pygame.draw.circle(screen, PURPLE_LIGHT, (center[0] + 13, center[1] - 4), 4)
        pygame.draw.arc(screen, PURPLE_LIGHT, (center[0] - 10, center[1] + 1, 20, 14), 0.15, math.pi - 0.15, 2)

        draw_text(screen, self.fonts["body"], self.voidling.name.upper(), (162, 50))
        draw_text(screen, self.fonts["tiny"], f"LV {self.voidling.level:02d}  //  {self.voidling.mood}", (163, 80), MUTED)
        draw_text(screen, self.fonts["tiny"], "XP", (163, 108), MUTED)
        draw_meter(screen, pygame.Rect(200, 109, 160, 12), self.voidling.xp_progress)
        draw_text(screen, self.fonts["tiny"], "EN", (163, 136), MUTED)
        draw_meter(screen, pygame.Rect(200, 137, 160, 12), self.voidling.energy_progress, GREEN)
        draw_text(screen, self.fonts["tiny"], "POCKET", (163, 169), PURPLE_LIGHT)
        for row, item in enumerate(self.voidling.inventory[:2]):
            draw_text(screen, self.fonts["tiny"], f"{item.name} x{item.quantity}", (163, 192 + row * 18), WHITE)

    def draw_game_context(self, screen):
        draw_text(screen, self.fonts["tiny"], "GAME // LIVE TELEMETRY", (18, 14), PURPLE_LIGHT)
        pygame.draw.line(screen, BODY_EDGE, (18, 36), (372, 36), 1)
        draw_text(screen, self.fonts["heading"], f"{self.game_score:02d}", (70, 90), WHITE, center=True)
        draw_text(screen, self.fonts["tiny"], "CAPTURED", (34, 119), MUTED)
        draw_text(screen, self.fonts["heading"], f"{self.game_misses:02d}", (70, 166), PURPLE_LIGHT, center=True)
        draw_text(screen, self.fonts["tiny"], "SIGNALS LOST", (25, 195), MUTED)
        draw_panel(screen, pygame.Rect(150, 53, 222, 157))
        draw_text(screen, self.fonts["small"], "FIELD GUIDE", (168, 70), PURPLE_LIGHT)
        draw_text(screen, self.fonts["tiny"], "MOVE THE RECEIVER", (168, 106), WHITE)
        draw_text(screen, self.fonts["tiny"], "UNDER EACH SIGNAL.", (168, 128), WHITE)
        draw_text(screen, self.fonts["tiny"], "SPEED RISES WITH SCORE.", (168, 158), MUTED)
        draw_text(screen, self.fonts["tiny"], "D-PAD  <  >", (168, 187), GREEN)

    def draw_settings_context(self, screen):
        label = SETTING_LABELS[self.module_index]
        descriptions = {
            "SCANLINES": ("DISPLAY FILTER", "Adds a subtle CRT-style texture."),
            "ANIMATIONS": ("MOTION SYSTEM", "Controls lightweight UI motion."),
            "STATUS DETAIL": ("DETAIL LEVEL", "Shows expanded device telemetry."),
        }
        title, description = descriptions[label]
        draw_text(screen, self.fonts["tiny"], "SETTINGS // LIVE PREVIEW", (18, 14), PURPLE_LIGHT)
        pygame.draw.line(screen, BODY_EDGE, (18, 36), (372, 36), 1)
        draw_panel(screen, pygame.Rect(18, 55, 354, 151))
        draw_text(screen, self.fonts["small"], title, (38, 74), WHITE)
        draw_text(screen, self.fonts["tiny"], description, (38, 109), MUTED)
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
        pygame.quit()
