from __future__ import annotations

import math

from zozode.player import Player


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def capped_sword_endpoint(
    player: Player,
    mouse_x: float,
    mouse_y: float,
    max_length: float,
) -> tuple[float, float]:
    dx = mouse_x - player.x
    dy = mouse_y - player.y
    length = math.hypot(dx, dy)
    if length == 0:
        return player.x, player.y
    scale = min(max_length, length) / length
    return player.x + dx * scale, player.y + dy * scale


def point_segment_distance(
    point_x: float,
    point_y: float,
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
) -> float:
    segment_x = end_x - start_x
    segment_y = end_y - start_y
    length_squared = segment_x * segment_x + segment_y * segment_y
    if length_squared == 0:
        return math.hypot(point_x - start_x, point_y - start_y)
    t = ((point_x - start_x) * segment_x + (point_y - start_y) * segment_y) / length_squared
    t = clamp(t, 0, 1)
    closest_x = start_x + t * segment_x
    closest_y = start_y + t * segment_y
    return math.hypot(point_x - closest_x, point_y - closest_y)
