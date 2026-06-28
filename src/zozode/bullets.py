from __future__ import annotations

import uuid

from zozode.constants import BULLET_LIFETIME, BULLET_SPEED, HEIGHT, WIDTH
from zozode.geometry import unit_vector
from zozode.player import Bullet, Player


def spawn_bullet(player: Player, mouse_pos: tuple[int, int]) -> Bullet:
    dx, dy = unit_vector(player.x, player.y, mouse_pos[0], mouse_pos[1])
    return Bullet(
        id=uuid.uuid4().hex,
        owner=player.name,
        x=player.x,
        y=player.y,
        vx=dx * BULLET_SPEED,
        vy=dy * BULLET_SPEED,
    )


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
