from __future__ import annotations

from typing import Any

import pygame

from zozode.constants import DOT_RADIUS, HEIGHT, SPEED, WIDTH
from zozode.geometry import capped_sword_endpoint, clamp
from zozode.player import Player


def update_remote_player(
    message: dict[str, Any],
    players: dict[str, Player],
    max_length: float,
) -> None:
    player_id = str(message.get('id'))
    if player_id not in players:
        return
    player = players[player_id]
    if not player.alive:
        return
    player.x = clamp(float(message.get('x', player.x)), DOT_RADIUS, WIDTH - DOT_RADIUS)
    player.y = clamp(float(message.get('y', player.y)), DOT_RADIUS, HEIGHT - DOT_RADIUS)
    mouse_x = float(message.get('mouse_x', player.sword_x))
    mouse_y = float(message.get('mouse_y', player.sword_y))
    player.sword_x, player.sword_y = capped_sword_endpoint(player, mouse_x, mouse_y, max_length)


def update_local_player(
    player: Player,
    keys: pygame.key.ScancodeWrapper,
    mouse_pos: tuple[int, int],
    dt: float,
    max_length: float,
) -> None:
    if not player.alive:
        return
    dx = float(keys[pygame.K_d]) - float(keys[pygame.K_a])
    dy = float(keys[pygame.K_s]) - float(keys[pygame.K_w])
    player.x = clamp(player.x + dx * SPEED * dt, DOT_RADIUS, WIDTH - DOT_RADIUS)
    player.y = clamp(player.y + dy * SPEED * dt, DOT_RADIUS, HEIGHT - DOT_RADIUS)
    player.sword_x, player.sword_y = capped_sword_endpoint(
        player,
        mouse_pos[0],
        mouse_pos[1],
        max_length,
    )
