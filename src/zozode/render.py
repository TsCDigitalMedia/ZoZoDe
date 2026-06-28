from __future__ import annotations

import time
from collections.abc import Iterable

import pygame

from zozode.constants import BULLET_RADIUS, DOT_RADIUS, ENEMY_RADIUS
from zozode.player import Enemy, Player


def draw(
    screen: pygame.Surface,
    font: pygame.font.Font,
    players: Iterable[Player],
    status: str,
    enemies: Iterable[Enemy] = (),
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
    text = font.render(status, True, (230, 230, 230))
    screen.blit(text, (12, 12))
    pygame.display.flip()
