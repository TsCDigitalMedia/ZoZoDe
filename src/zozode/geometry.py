from __future__ import annotations

import math

from zozode.player import Player


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def unit_vector(start_x: float, start_y: float, end_x: float, end_y: float) -> tuple[float, float]:
    dx = end_x - start_x
    dy = end_y - start_y
    length = math.hypot(dx, dy)
    if length == 0:
        return 1.0, 0.0
    return dx / length, dy / length


def indicator_endpoint(
    player: Player,
    mouse_x: float,
    mouse_y: float,
    length: float,
) -> tuple[float, float]:
    dx, dy = unit_vector(player.x, player.y, mouse_x, mouse_y)
    return player.x + dx * length, player.y + dy * length
