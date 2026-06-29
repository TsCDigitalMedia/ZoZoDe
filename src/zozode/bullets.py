from __future__ import annotations

import math
import random
import uuid

from zozode.assets import WeaponConfig, load_default_weapon
from zozode.constants import BULLET_LIFETIME, BULLET_SPEED
from zozode.geometry import unit_vector
from zozode.level import DEFAULT_LEVEL, Level
from zozode.player import Bullet, Player

DEFAULT_WEAPON = load_default_weapon()


def default_on_success_shoot() -> bool:
    return True


def shot_interval_seconds(player: Player, weapon: WeaponConfig = DEFAULT_WEAPON) -> float:
    rps = max(0.1, weapon.rps * player.statistics.rps_multiplier)
    return 1 / rps


def spawn_bullet(
    player: Player,
    mouse_pos: tuple[int, int],
    weapon: WeaponConfig = DEFAULT_WEAPON,
) -> Bullet:
    dx, dy = unit_vector(player.x, player.y, mouse_pos[0], mouse_pos[1])
    if weapon.spread:
        angle = math.atan2(dy, dx) + random.uniform(-weapon.spread, weapon.spread)
        dx = math.cos(angle)
        dy = math.sin(angle)
    return Bullet(
        id=uuid.uuid4().hex,
        owner=player.name,
        x=player.x,
        y=player.y,
        vx=dx * BULLET_SPEED,
        vy=dy * BULLET_SPEED,
        damage=max(1, round(weapon.damage * player.statistics.damage_multiplier)),
    )


def maybe_spawn_bullet(
    player: Player,
    mouse_pos: tuple[int, int],
    now: float,
    next_shot_at: float,
    weapon: WeaponConfig = DEFAULT_WEAPON,
    on_success_shoot=default_on_success_shoot,
) -> tuple[Bullet | None, float]:
    if not player.alive or now < next_shot_at:
        return None, next_shot_at
    if not on_success_shoot():
        return None, next_shot_at
    return spawn_bullet(player, mouse_pos, weapon), now + shot_interval_seconds(player, weapon)


def step_bullets(players: dict[str, Player], dt: float, level: Level = DEFAULT_LEVEL) -> None:
    for player in players.values():
        active = []
        for bullet in player.bullets:
            bullet.x += bullet.vx * dt
            bullet.y += bullet.vy * dt
            bullet.age += dt
            if (
                level.in_bounds(bullet.x, bullet.y)
                and not level.contains_obstacle(bullet.x, bullet.y)
                and bullet.age <= BULLET_LIFETIME
            ):
                active.append(bullet)
        player.bullets = active
