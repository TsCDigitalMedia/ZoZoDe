from __future__ import annotations

from zozode.constants import ARENA_HEIGHT, ARENA_WIDTH, HEIGHT, WIDTH
from zozode.geometry import clamp
from zozode.player import Player


def camera_offset(player: Player) -> tuple[float, float]:
    x = clamp(player.x - WIDTH / 2, 0, max(0, ARENA_WIDTH - WIDTH))
    y = clamp(player.y - HEIGHT / 2, 0, max(0, ARENA_HEIGHT - HEIGHT))
    return x, y


def screen_to_world(screen_pos: tuple[int, int], offset: tuple[float, float]) -> tuple[int, int]:
    return round(screen_pos[0] + offset[0]), round(screen_pos[1] + offset[1])


def world_to_screen(x: float, y: float, offset: tuple[float, float]) -> tuple[int, int]:
    return round(x - offset[0]), round(y - offset[1])
