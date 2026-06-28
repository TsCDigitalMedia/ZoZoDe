from __future__ import annotations

import math
import random
import uuid

from zozode.assets import WeaponConfig, load_default_weapon
from zozode.constants import BULLET_LIFETIME, BULLET_SPEED, HEIGHT, WIDTH
from zozode.geometry import unit_vector
from zozode.player import Bullet, Player

DEFAULT_WEAPON = load_default_weapon()


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
    )


def maybe_spawn_bullet(
    player: Player,
    mouse_pos: tuple[int, int],
    now: float,
    next_shot_at: float,
    weapon: WeaponConfig = DEFAULT_WEAPON,
) -> tuple[Bullet | None, float]:
    if not player.alive or now < next_shot_at:
        return None, next_shot_at
    return spawn_bullet(player, mouse_pos, weapon), now + weapon.shot_interval_seconds


def step_bullets(players: dict[str, Player], dt: float) -> None:
    for player in players.values():
        active = []
        for bullet in player.bullets:
            bullet.x += bullet.vx * dt
            bullet.y += bullet.vy * dt
            bullet.age += dt
            if 0 <= bullet.x <= WIDTH and 0 <= bullet.y <= HEIGHT and bullet.age <= BULLET_LIFETIME:
                active.append(bullet)
        player.bullets = active
