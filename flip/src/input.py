"""Hardware-independent named input actions."""

from enum import Enum


class Action(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    A = "select"
    B = "back"
    X = "x"
    Y = "y"
    START = "pause"
    SELECT = "select_menu"
    HOME = "home"
    BACK = "back"
    RESTART = "restart"
    QUIT = "quit"


def keyboard_action(key: int, pygame_module):
    mapping = {
        pygame_module.K_UP: Action.UP, pygame_module.K_w: Action.UP,
        pygame_module.K_DOWN: Action.DOWN, pygame_module.K_s: Action.DOWN,
        pygame_module.K_LEFT: Action.LEFT, pygame_module.K_a: Action.LEFT,
        pygame_module.K_RIGHT: Action.RIGHT, pygame_module.K_d: Action.RIGHT,
        pygame_module.K_RETURN: Action.A, pygame_module.K_SPACE: Action.A,
        pygame_module.K_ESCAPE: Action.B, pygame_module.K_BACKSPACE: Action.B,
        pygame_module.K_r: Action.RESTART, pygame_module.K_p: Action.START,
        pygame_module.K_x: Action.X, pygame_module.K_y: Action.Y,
        pygame_module.K_TAB: Action.SELECT, pygame_module.K_h: Action.HOME,
        pygame_module.K_q: Action.QUIT,
    }
    return mapping.get(key)
