from __future__ import annotations

from dataclasses import dataclass

import pygame

from zozode.constants import HEIGHT, WIDTH
from zozode.magazine import DEFAULT_AMMO, MagazineState
from zozode.player import Player

POWERUP_UNLOCK_SCORE = 30
RPS_MULTIPLIER = 2.0
HEALTH_MULTIPLIER = 2
DAMAGE_MULTIPLIER = 2.0


@dataclass(frozen=True, slots=True)
class PowerUpOption:
    id: str
    label: str
    cost: int


POWERUP_OPTIONS = (
    PowerUpOption("rps", "Increase RPS", 30),
    PowerUpOption("health", "Increase Health", 60),
    PowerUpOption("damage", "Increase Damage", 90),
    PowerUpOption("ammo", "Refill Ammo", 10),
)


def should_show_powerups(score: int) -> bool:
    return score >= POWERUP_UNLOCK_SCORE


def powerup_button_rects() -> dict[str, pygame.Rect]:
    square_size = 112
    gap = 18
    total_width = square_size * 3 + gap * 2
    top = HEIGHT // 2 - 86
    left = WIDTH // 2 - total_width // 2
    rects = {
        option.id: pygame.Rect(left + index * (square_size + gap), top, square_size, square_size)
        for index, option in enumerate(POWERUP_OPTIONS[:3])
    }
    rects["ammo"] = pygame.Rect(WIDTH // 2 - 112, top + square_size + 22, 224, 44)
    return rects


def powerup_at(pos: tuple[int, int]) -> str | None:
    for powerup_id, rect in powerup_button_rects().items():
        if rect.collidepoint(pos):
            return powerup_id
    return None


def powerup_by_id(powerup_id: str) -> PowerUpOption | None:
    for option in POWERUP_OPTIONS:
        if option.id == powerup_id:
            return option
    return None


def apply_powerup(player: Player, magazine: MagazineState, powerup_id: str) -> bool:
    option = powerup_by_id(powerup_id)
    if option is None or player.statistics.score < option.cost:
        return False

    if option.id == "rps":
        player.statistics.rps_multiplier *= RPS_MULTIPLIER
    elif option.id == "health":
        player.health *= HEALTH_MULTIPLIER
        player.statistics.health = player.health
    elif option.id == "damage":
        player.statistics.damage_multiplier *= DAMAGE_MULTIPLIER
    elif option.id == "ammo":
        magazine.ammo = DEFAULT_AMMO

    player.statistics.score -= option.cost
    return True
