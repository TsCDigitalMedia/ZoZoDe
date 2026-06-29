from __future__ import annotations

from typing import Any

import pygame

from zozode.constants import DOT_RADIUS, INDICATOR_LENGTH, SPEED
from zozode.geometry import clamp, indicator_endpoint
from zozode.level import DEFAULT_LEVEL, Level
from zozode.player import Player


def update_remote_player(
    message: dict[str, Any],
    players: dict[str, Player],
    level: Level = DEFAULT_LEVEL,
) -> None:
    player_id = str(message.get("id"))
    if player_id not in players:
        return
    player = players[player_id]
    if not player.alive:
        return
    move_player_on_ground(
        player,
        float(message.get("x", player.x)),
        float(message.get("y", player.y)),
        level,
    )
    mouse_x = float(message.get("mouse_x", player.indicator_x))
    mouse_y = float(message.get("mouse_y", player.indicator_y))
    player.indicator_x, player.indicator_y = indicator_endpoint(
        player,
        mouse_x,
        mouse_y,
        INDICATOR_LENGTH,
    )


def update_local_player(
    player: Player,
    keys: pygame.key.ScancodeWrapper,
    mouse_pos: tuple[int, int],
    dt: float,
    level: Level = DEFAULT_LEVEL,
) -> None:
    if not player.alive:
        return
    dx = float(keys[pygame.K_d]) - float(keys[pygame.K_a])
    dy = float(keys[pygame.K_s]) - float(keys[pygame.K_w])
    move_player_on_ground(player, player.x + dx * SPEED * dt, player.y + dy * SPEED * dt, level)
    player.indicator_x, player.indicator_y = indicator_endpoint(
        player,
        mouse_pos[0],
        mouse_pos[1],
        INDICATOR_LENGTH,
    )


def move_player_on_ground(player: Player, x: float, y: float, level: Level = DEFAULT_LEVEL) -> None:
    x = clamp(x, DOT_RADIUS, level.width - DOT_RADIUS)
    y = clamp(y, DOT_RADIUS, level.height - DOT_RADIUS)
    if level.can_walk(x, y, DOT_RADIUS):
        player.x = x
        player.y = y
    elif level.can_walk(x, player.y, DOT_RADIUS):
        player.x = x
    elif level.can_walk(player.x, y, DOT_RADIUS):
        player.y = y


def lerp_remote_player(target: Player, source: Player, amount: float = 0.35) -> None:
    target.x += (source.x - target.x) * amount
    target.y += (source.y - target.y) * amount
    target.indicator_x += (source.indicator_x - target.indicator_x) * amount
    target.indicator_y += (source.indicator_y - target.indicator_y) * amount
    target.color = source.color
    target.indicator_color = source.indicator_color
    target.health = source.health
    target.invulnerable_until = source.invulnerable_until
    target.respawn_at = source.respawn_at
    target.alive = source.alive
    target.bullets = source.bullets
