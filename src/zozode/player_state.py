from __future__ import annotations

import random
import time
from dataclasses import asdict
from typing import Any

from zozode.colors import random_color
from zozode.constants import DOT_RADIUS, HEALTH, HEIGHT, WIDTH
from zozode.player import Player


def spawn_player(name: str) -> Player:
    x = random.randint(DOT_RADIUS, WIDTH - DOT_RADIUS)
    y = random.randint(DOT_RADIUS, HEIGHT - DOT_RADIUS)
    return Player(
        name=name,
        x=x,
        y=y,
        color=random_color(),
        sword_color=random_color(),
        sword_x=x,
        sword_y=y,
        health=HEALTH,
    )


def player_payload(player: Player) -> dict[str, Any]:
    payload = asdict(player)
    now = time.monotonic()
    payload['color'] = list(player.color)
    payload['sword_color'] = list(player.sword_color)
    payload['invulnerable_remaining'] = max(0.0, player.invulnerable_until - now)
    return payload


def player_from_payload(payload: dict[str, Any]) -> Player:
    color = payload.get('color', [255, 255, 255])
    sword_color = payload.get('sword_color', color)
    return Player(
        name=str(payload['name']),
        x=float(payload['x']),
        y=float(payload['y']),
        color=(int(color[0]), int(color[1]), int(color[2])),
        sword_color=(int(sword_color[0]), int(sword_color[1]), int(sword_color[2])),
        sword_x=float(payload.get('sword_x', payload['x'])),
        sword_y=float(payload.get('sword_y', payload['y'])),
        health=int(payload.get('health', HEALTH)),
        invulnerable_until=time.monotonic()
        + float(payload.get('invulnerable_remaining', 0)),
        respawn_at=float(payload.get('respawn_at', 0)),
        alive=bool(payload.get('alive', True)),
    )


def copy_player_state(target: Player, source: Player) -> None:
    target.x = source.x
    target.y = source.y
    target.color = source.color
    target.sword_color = source.sword_color
    target.sword_x = source.sword_x
    target.sword_y = source.sword_y
    target.health = source.health
    target.invulnerable_until = source.invulnerable_until
    target.respawn_at = source.respawn_at
    target.alive = source.alive
