from __future__ import annotations

import math
import time
from collections.abc import Iterable

import pygame

from zozode.ammo import AmmoState, reload_progress
from zozode.constants import BULLET_RADIUS, DOT_RADIUS, ENEMY_RADIUS, HEIGHT
from zozode.player import Enemy, Player


def draw(
    screen: pygame.Surface,
    font: pygame.font.Font,
    players: Iterable[Player],
    status: str,
    enemies: Iterable[Enemy] = (),
    ammo: AmmoState | None = None,
) -> None:
    now = time.monotonic()
    screen.fill((20, 20, 24))
    for enemy in enemies:
        pygame.draw.circle(screen, (230, 20, 20), (round(enemy.x), round(enemy.y)), ENEMY_RADIUS)
    for player in players:
        for bullet in player.bullets:
            pygame.draw.circle(
                screen,
                player.indicator_color,
                (round(bullet.x), round(bullet.y)),
                BULLET_RADIUS,
            )
        if not player.alive:
            continue
        blinking = player.invulnerable_until > now and int(now * 10) % 2 == 0
        if blinking:
            continue
        pygame.draw.line(
            screen,
            player.indicator_color,
            (round(player.x), round(player.y)),
            (round(player.indicator_x), round(player.indicator_y)),
            3,
        )
        pygame.draw.circle(screen, player.color, (round(player.x), round(player.y)), DOT_RADIUS)
        health = font.render(str(player.health), True, (240, 240, 240))
        screen.blit(health, (round(player.x) - 5, round(player.y) - 30))
    if ammo is not None:
        draw_ammo(screen, ammo, now)
    text = font.render(status, True, (230, 230, 230))
    screen.blit(text, (12, 12))
    pygame.display.flip()


def draw_ammo(screen: pygame.Surface, ammo: AmmoState, now: float) -> None:
    center = (44, HEIGHT - 44)
    radius = 24
    rect = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
    pygame.draw.circle(screen, (70, 70, 76), center, radius, 2)
    if ammo.reload_started_at:
        progress = reload_progress(ammo, now)
        pygame.draw.arc(
            screen,
            (240, 240, 240),
            rect,
            -math.pi / 2,
            -math.pi / 2 + math.tau * progress,
            4,
        )
        return

    count = max(1, ammo.weapon.ammo)
    remaining = max(0, ammo.remaining or 0)
    gap = 0.08
    segment = max(0.02, (math.tau / count) - gap)
    for index in range(count):
        start = -math.pi / 2 + index * math.tau / count
        color = (240, 240, 240) if index < remaining else (70, 70, 76)
        pygame.draw.arc(screen, color, rect, start, start + segment, 4)
