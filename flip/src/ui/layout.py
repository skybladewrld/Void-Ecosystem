"""Pure layout helpers used by scrollable device screens."""

from __future__ import annotations


def clamp_selection(selected: int, count: int) -> int:
    return 0 if count <= 0 else max(0, min(int(selected), count - 1))


def scroll_window(selected: int, count: int, visible: int) -> tuple[int, int]:
    if count <= 0 or visible <= 0:
        return 0, 0
    selected = clamp_selection(selected, count)
    visible = min(visible, count)
    start = max(0, min(selected - visible + 1, count - visible))
    return start, start + visible


def wrap_words(text: str, measure, max_width: int, max_lines: int = 3) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        measured = measure(candidate)
        width = measured[0] if isinstance(measured, tuple) else measured
        if current and width > max_width:
            lines.append(current)
            current = word
            if len(lines) == max_lines:
                break
        else:
            current = candidate
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and len(" ".join(lines).split()) < len(words):
        lines[-1] = lines[-1].rstrip(".") + "..."
    return lines


def board_to_visual(square: tuple[int, int], human_at_bottom: bool = True) -> tuple[int, int]:
    row, col = square
    return (7 - row, 7 - col) if human_at_bottom else square


def visual_delta_to_board(delta: tuple[int, int], human_at_bottom: bool = True) -> tuple[int, int]:
    dr, dc = delta
    return (-dr, -dc) if human_at_bottom else (dr, dc)


def capture_required(moves) -> bool:
    return any(bool(move.captures) for move in moves)


def recipe_availability(recipe, inventory: dict[str, int], owned: list[str], locked: bool = False) -> tuple[bool, str]:
    if recipe.relic_id in owned:
        return False, "OWNED"
    if locked:
        return False, "LOCKED"
    missing = [item_id for item_id, quantity in recipe.ingredients.items() if inventory.get(item_id, 0) < quantity]
    return (False, "MISSING MATERIALS") if missing else (True, "READY TO CRAFT")
