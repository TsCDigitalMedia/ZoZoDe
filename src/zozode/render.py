from __future__ import annotations

import time
from collections.abc import Iterable

import pygame

from zozode.constants import DOT_RADIUS
from zozode.player import Player


def draw(
    screen: pygame.Surface,
    font: pygame.font.Font,
    players: Iterable[Player],
    status: str,
) -> None:
    now = time.monotonic()
    screen.fill((20, 20, 24))
    for player in players:
        if not player.alive:
            continue
        blinking = player.invulnerable_until > now and int(now * 10) % 2 == 0
        if blinking:
            continue
        pygame.draw.line(
            screen,
            player.sword_color,
            (round(player.x), round(player.y)),
            (round(player.sword_x), round(player.sword_y)),
            4,
        )
        pygame.draw.circle(screen, player.color, (round(player.x), round(player.y)), DOT_RADIUS)
        health = font.render(str(player.health), True, (240, 240, 240))
        screen.blit(health, (round(player.x) - 5, round(player.y) - 30))
    text = font.render(status, True, (230, 230, 230))
    screen.blit(text, (12, 12))
    pygame.display.flip()
