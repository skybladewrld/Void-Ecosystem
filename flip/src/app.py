"""Core Void Flip simulator state, input, and rendering."""

import math
import time
from pathlib import Path

import pygame

from models import Voidling
from theme import (
    BLACK, BODY, BODY_EDGE, GREEN, MUTED, PANEL_LIGHT, PURPLE, PURPLE_DARK,
    PURPLE_LIGHT, SCREEN, WHITE, draw_meter, draw_panel, draw_text, make_fonts,
)


WINDOW_SIZE = (1200, 900)
TOP_SCREEN = pygame.Rect(210, 78, 780, 386)
BOTTOM_SCREEN = pygame.Rect(405, 572, 390, 242)
MENU_ITEMS = ("GAMES", "EMULATORS", "FRIENDS", "TRADING", "SETTINGS")

MODULE_COPY = {
    "GAMES": ("GAME LIBRARY", "Installed Void games will appear here.", "No games installed  //  v0.1 placeholder"),
    "EMULATORS": ("EMULATOR BAY", "Configured systems and launchers will live here.", "No emulators configured  //  v0.1 placeholder"),
    "FRIENDS": ("FRIEND LINK", "Local presence and direct connections will appear here.", "OFFLINE  //  local profile only"),
    "TRADING": ("TRADE TERMINAL", "Validated item trades will be managed here.", "LOCKED  //  trusted services not implemented"),
    "SETTINGS": ("SYSTEM SETTINGS", "Display, audio, controls, and device options.", "DESKTOP SIMULATOR  //  build 0.1"),
}


class VoidFlipApp:
    """A single app object that can later accept hardware input adapters."""

    def __init__(self, *, show_splash=True):
        pygame.init()
        pygame.display.set_caption("Void Flip v0.1")
        self.surface = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.fonts = make_fonts()
        self.voidling = Voidling()
        self.running = True
        self.page = "HOME"
        self.selected_index = 0
        self.started_at = time.monotonic()
        self.show_splash = show_splash
        self.splash_duration = 2.35
        self.transition = 0.0

    def handle_action(self, action):
        """Update navigation without depending on a particular input device."""

        if action == "quit":
            self.running = False
        elif action == "back" and self.page != "HOME":
            self.page = "HOME"
            self.transition = 1.0
        elif action == "up" and self.page == "HOME":
            self.selected_index = (self.selected_index - 1) % len(MENU_ITEMS)
        elif action == "down" and self.page == "HOME":
            self.selected_index = (self.selected_index + 1) % len(MENU_ITEMS)
        elif action == "select" and self.page == "HOME":
            self.page = MENU_ITEMS[self.selected_index]
            self.transition = 1.0

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

    def draw(self):
        elapsed = time.monotonic() - self.started_at
        self.surface.fill(BLACK)
        if self.show_splash and elapsed < self.splash_duration:
            self.draw_splash(elapsed / self.splash_duration)
        else:
            self.draw_console(elapsed)
        pygame.display.flip()

    def draw_splash(self, progress):
        glow = int(95 + 45 * math.sin(progress * math.pi))
        draw_text(self.surface, self.fonts["title"], "VOID", (600, 390), (190, glow, 255), center=True)
        draw_text(self.surface, self.fonts["small"], "FLIP SYSTEM // INITIALIZING", (600, 456), MUTED, center=True)
        bar = pygame.Rect(420, 500, 360, 8)
        pygame.draw.rect(self.surface, (29, 26, 38), bar)
        pygame.draw.rect(self.surface, PURPLE, (bar.x, bar.y, int(bar.width * progress), bar.height))
        for x in range(bar.x, bar.right, 24):
            pygame.draw.line(self.surface, BLACK, (x, bar.y), (x, bar.bottom), 1)
        draw_text(self.surface, self.fonts["tiny"], f"BOOT {int(progress * 100):02d}%", (600, 530), PURPLE_LIGHT, center=True)

    def draw_console(self, elapsed):
        self.draw_body()
        top = self.surface.subsurface(TOP_SCREEN)
        bottom = self.surface.subsurface(BOTTOM_SCREEN)
        top.fill(SCREEN)
        bottom.fill(SCREEN)
        self.draw_home(top) if self.page == "HOME" else self.draw_module(top)
        self.draw_voidling_screen(bottom, elapsed)
        self.draw_controls()
        if self.transition > 0:
            veil = pygame.Surface(TOP_SCREEN.size, pygame.SRCALPHA)
            veil.fill((153, 86, 255, int(self.transition * 70)))
            top.blit(veil, (0, 0))

    def draw_body(self):
        top_body = pygame.Rect(165, 35, 870, 472)
        lower_body = pygame.Rect(92, 520, 1016, 342)
        pygame.draw.rect(self.surface, BODY, top_body, border_radius=22)
        pygame.draw.rect(self.surface, BODY_EDGE, top_body, 2, border_radius=22)
        pygame.draw.rect(self.surface, BODY, lower_body, border_radius=28)
        pygame.draw.rect(self.surface, BODY_EDGE, lower_body, 2, border_radius=28)
        pygame.draw.rect(self.surface, (9, 10, 14), (210, 502, 780, 32))
        pygame.draw.line(self.surface, PURPLE_DARK, (245, 518), (955, 518), 2)
        pygame.draw.rect(self.surface, (2, 3, 6), TOP_SCREEN.inflate(12, 12), border_radius=4)
        pygame.draw.rect(self.surface, PURPLE_DARK, TOP_SCREEN.inflate(12, 12), 2, border_radius=4)
        pygame.draw.rect(self.surface, (2, 3, 6), BOTTOM_SCREEN.inflate(12, 12), border_radius=4)
        pygame.draw.rect(self.surface, BODY_EDGE, BOTTOM_SCREEN.inflate(12, 12), 2, border_radius=4)
        pygame.draw.circle(self.surface, PURPLE_DARK, (600, 58), 3)
        draw_text(self.surface, self.fonts["tiny"], "VOID // FLIP", (497, 836), MUTED)

    def draw_home(self, screen):
        draw_text(screen, self.fonts["small"], "VOID SHELL", (34, 25), PURPLE_LIGHT)
        draw_text(screen, self.fonts["heading"], "HOME", (34, 50))
        draw_text(screen, self.fonts["tiny"], "LOCAL MODE", (650, 30), GREEN)
        pygame.draw.line(screen, BODY_EDGE, (34, 96), (746, 96), 1)
        for index, label in enumerate(MENU_ITEMS):
            y = 116 + index * 48
            selected = index == self.selected_index
            rect = pygame.Rect(34, y, 438, 38)
            if selected:
                pygame.draw.rect(screen, PURPLE_DARK, rect)
                pygame.draw.rect(screen, PURPLE, rect, 1)
                pygame.draw.polygon(screen, PURPLE_LIGHT, [(rect.x + 12, y + 12), (rect.x + 20, y + 19), (rect.x + 12, y + 26)])
            draw_text(screen, self.fonts["body"], label, (68, y + 7), WHITE if selected else MUTED)

        status = pygame.Rect(500, 116, 246, 230)
        draw_panel(screen, status)
        draw_text(screen, self.fonts["tiny"], "SYSTEM STATUS", (520, 134), PURPLE_LIGHT)
        for row, (label, value) in enumerate((("PROFILE", "LOCAL"), ("NETWORK", "OFFLINE"), ("NODE", "NONE"), ("BUILD", "0.1"))):
            y = 174 + row * 34
            draw_text(screen, self.fonts["tiny"], label, (520, y), MUTED)
            draw_text(screen, self.fonts["tiny"], value, (632, y), WHITE)
        draw_text(screen, self.fonts["tiny"], "ENTER  SELECT", (520, 318), MUTED)

    def draw_module(self, screen):
        title, description, status = MODULE_COPY[self.page]
        draw_text(screen, self.fonts["small"], f"VOID SHELL / {self.page}", (34, 25), PURPLE_LIGHT)
        draw_text(screen, self.fonts["heading"], title, (34, 55))
        pygame.draw.line(screen, BODY_EDGE, (34, 103), (746, 103), 1)
        panel = pygame.Rect(34, 128, 712, 178)
        draw_panel(screen, panel)
        draw_text(screen, self.fonts["body"], description, (58, 158))
        draw_text(screen, self.fonts["small"], status, (58, 204), MUTED)
        pygame.draw.line(screen, PURPLE_DARK, (58, 248), (722, 248), 1)
        draw_text(screen, self.fonts["tiny"], "MODULE CONNECTION READY FOR FUTURE IMPLEMENTATION", (58, 268), PURPLE_LIGHT)
        draw_text(screen, self.fonts["small"], "ESC / BACKSPACE  RETURN HOME", (34, 337), MUTED)

    def draw_voidling_screen(self, screen, elapsed):
        draw_text(screen, self.fonts["tiny"], "VOIDLING // COMPANION LINK", (18, 14), PURPLE_LIGHT)
        pygame.draw.line(screen, BODY_EDGE, (18, 36), (372, 36), 1)

        bob = int(math.sin(elapsed * 2.3) * 4)
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

        draw_text(screen, self.fonts["body"], self.voidling.name.upper(), (162, 52))
        draw_text(screen, self.fonts["tiny"], f"LV {self.voidling.level:02d}  //  {self.voidling.mood}", (163, 82), MUTED)
        draw_text(screen, self.fonts["tiny"], "XP", (163, 112), MUTED)
        draw_meter(screen, pygame.Rect(200, 113, 160, 12), self.voidling.xp_progress)
        draw_text(screen, self.fonts["tiny"], "EN", (163, 140), MUTED)
        draw_meter(screen, pygame.Rect(200, 141, 160, 12), self.voidling.energy_progress, GREEN)
        draw_text(screen, self.fonts["tiny"], "MINI INVENTORY", (163, 174), PURPLE_LIGHT)
        for row, item in enumerate(self.voidling.inventory[:2]):
            draw_text(screen, self.fonts["tiny"], f"{item.name} x{item.quantity}", (163, 197 + row * 18), WHITE)

    def draw_controls(self):
        # D-pad
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
