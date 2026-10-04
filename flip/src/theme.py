"""Void Flip colors and lightweight drawing helpers."""

import pygame


BLACK = (5, 6, 10)
BODY = (14, 15, 21)
BODY_EDGE = (40, 41, 52)
SCREEN = (7, 8, 13)
PANEL = (16, 17, 25)
PANEL_LIGHT = (23, 24, 35)
PURPLE = (153, 86, 255)
PURPLE_LIGHT = (195, 151, 255)
PURPLE_DARK = (74, 38, 126)
WHITE = (230, 226, 239)
MUTED = (129, 126, 145)
GREEN = (82, 212, 153)


def make_fonts() -> dict[str, pygame.font.Font]:
    """Use system fonts so the prototype has no external asset dependency."""

    return {
        "tiny": pygame.font.SysFont("consolas", 14),
        "small": pygame.font.SysFont("consolas", 18),
        "body": pygame.font.SysFont("consolas", 22),
        "heading": pygame.font.SysFont("consolas", 31, bold=True),
        "title": pygame.font.SysFont("consolas", 64, bold=True),
    }


def draw_text(surface, font, text, position, color=WHITE, *, center=False):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=position) if center else rendered.get_rect(topleft=position)
    surface.blit(rendered, rect)
    return rect


def draw_panel(surface, rect, *, fill=PANEL, border=BODY_EDGE, accent=PURPLE):
    """Draw a squared panel with clipped cyberpunk corner marks."""

    pygame.draw.rect(surface, fill, rect)
    pygame.draw.rect(surface, border, rect, 1)
    mark = 14
    pygame.draw.line(surface, accent, rect.topleft, (rect.left + mark, rect.top), 2)
    pygame.draw.line(surface, accent, rect.topleft, (rect.left, rect.top + mark), 2)
    pygame.draw.line(surface, accent, rect.bottomright, (rect.right - mark, rect.bottom), 2)
    pygame.draw.line(surface, accent, rect.bottomright, (rect.right, rect.bottom - mark), 2)


def draw_meter(surface, rect, progress, color=PURPLE):
    pygame.draw.rect(surface, (30, 30, 42), rect)
    inner = rect.inflate(-4, -4)
    width = int(inner.width * max(0.0, min(1.0, progress)))
    if width:
        pygame.draw.rect(surface, color, (inner.x, inner.y, width, inner.height))
    pygame.draw.rect(surface, BODY_EDGE, rect, 1)
