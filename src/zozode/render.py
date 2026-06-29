from __future__ import annotations

import math
import time
from collections.abc import Iterable

import pygame

from zozode.camera import camera_offset, world_to_screen
from zozode.constants import (
    ARENA_HEIGHT,
    ARENA_WIDTH,
    BULLET_RADIUS,
    DOT_RADIUS,
    ENEMY_RADIUS,
    HEIGHT,
)
from zozode.magazine import MagazineState, reload_progress
from zozode.player import Enemy, Player


def draw(
    screen: pygame.Surface,
    font: pygame.font.Font,
    players: Iterable[Player],
    status: str,
    enemies: Iterable[Enemy] = (),
    magazine: MagazineState | None = None,
    camera_player: Player | None = None,
) -> None:
    now = time.monotonic()
    offset = camera_offset(camera_player) if camera_player is not None else (0.0, 0.0)
    screen.fill((20, 20, 24))
    arena_rect = pygame.Rect(round(-offset[0]), round(-offset[1]), ARENA_WIDTH, ARENA_HEIGHT)
    pygame.draw.rect(screen, (55, 55, 64), arena_rect, 2)
    for enemy in enemies:
        pygame.draw.circle(
            screen,
            (230, 20, 20),
            world_to_screen(enemy.x, enemy.y, offset),
            ENEMY_RADIUS,
        )
    for player in players:
        for bullet in player.bullets:
            pygame.draw.circle(
                screen,
                player.indicator_color,
                world_to_screen(bullet.x, bullet.y, offset),
                BULLET_RADIUS,
            )
        if not player.alive:
            continue
        blinking = player.invulnerable_until > now and int(now * 10) % 2 == 0
        if blinking:
            continue
        player_pos = world_to_screen(player.x, player.y, offset)
        pygame.draw.line(
            screen,
            player.indicator_color,
            player_pos,
            world_to_screen(player.indicator_x, player.indicator_y, offset),
            3,
        )
        pygame.draw.circle(screen, player.color, player_pos, DOT_RADIUS)
        health = font.render(str(player.health), True, (240, 240, 240))
        screen.blit(health, (player_pos[0] - 5, player_pos[1] - 30))
    if magazine is not None:
        draw_magazine(screen, magazine, now)
    text = font.render(status, True, (230, 230, 230))
    screen.blit(text, (12, 12))
    pygame.display.flip()


def draw_magazine(screen: pygame.Surface, magazine: MagazineState, now: float) -> None:
    center = (44, HEIGHT - 44)
    radius = 24
    rect = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
    pygame.draw.circle(screen, (70, 70, 76), center, radius, 2)
    if magazine.reload_started_at:
        progress = reload_progress(magazine, now)
        pygame.draw.arc(
            screen,
            (240, 240, 240),
            rect,
            -math.pi / 2,
            -math.pi / 2 + math.tau * progress,
            4,
        )
        return

    count = max(1, magazine.weapon.magazine)
    remaining = max(0, magazine.remaining or 0)
    gap = 0.08
    segment = max(0.02, (math.tau / count) - gap)
    for index in range(count):
        start = -math.pi / 2 + index * math.tau / count
        color = (240, 240, 240) if index < remaining else (70, 70, 76)
        pygame.draw.arc(screen, color, rect, start, start + segment, 4)
