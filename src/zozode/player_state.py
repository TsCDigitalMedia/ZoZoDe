from __future__ import annotations

import math
import random
import time
import uuid
from dataclasses import asdict
from typing import Any

from zozode.assets import EnemyConfig, load_basic_enemy
from zozode.colors import random_color
from zozode.constants import ARENA_HEIGHT, ARENA_WIDTH, DOT_RADIUS, ENEMY_RADIUS, HEALTH
from zozode.geometry import unit_vector
from zozode.player import Bullet, Enemy, Player

ENEMY_CONFIG = load_basic_enemy()


def spawn_player(name: str) -> Player:
    x = random.randint(DOT_RADIUS, ARENA_WIDTH - DOT_RADIUS)
    y = random.randint(DOT_RADIUS, ARENA_HEIGHT - DOT_RADIUS)
    return Player(
        name=name,
        x=x,
        y=y,
        color=random_color(),
        indicator_color=random_color(),
        indicator_x=x,
        indicator_y=y,
        health=HEALTH,
    )


def spawn_enemy(
    players: dict[str, Player],
    config: EnemyConfig = ENEMY_CONFIG,
    kind: str = "basic",
) -> Enemy | None:
    targets = [player for player in players.values() if player.alive]
    if not targets:
        return None
    edge = random.randrange(4)
    if edge == 0:
        x = random.uniform(0, ARENA_WIDTH)
        y = -ENEMY_RADIUS
    elif edge == 1:
        x = ARENA_WIDTH + ENEMY_RADIUS
        y = random.uniform(0, ARENA_HEIGHT)
    elif edge == 2:
        x = random.uniform(0, ARENA_WIDTH)
        y = ARENA_HEIGHT + ENEMY_RADIUS
    else:
        x = -ENEMY_RADIUS
        y = random.uniform(0, ARENA_HEIGHT)
    nearest_distance = min(math.hypot(player.x - x, player.y - y) for player in targets)
    nearest_targets = [
        player for player in targets if math.hypot(player.x - x, player.y - y) == nearest_distance
    ]
    target = random.choice(nearest_targets)
    vx, vy = unit_vector(x, y, target.x, target.y)
    return Enemy(
        id=uuid.uuid4().hex,
        x=x,
        y=y,
        vx=vx,
        vy=vy,
        target=target.name,
        kind=kind,
        health=config.health,
        speed=config.speed,
        gain=config.gain,
    )


def bullet_payload(bullet: Bullet) -> dict[str, Any]:
    return asdict(bullet)


def bullet_from_payload(payload: dict[str, Any]) -> Bullet:
    return Bullet(
        id=str(payload["id"]),
        owner=str(payload["owner"]),
        x=float(payload["x"]),
        y=float(payload["y"]),
        vx=float(payload["vx"]),
        vy=float(payload["vy"]),
        age=float(payload.get("age", 0)),
    )


def enemy_payload(enemy: Enemy) -> dict[str, Any]:
    return asdict(enemy)


def enemy_from_payload(payload: dict[str, Any]) -> Enemy:
    return Enemy(
        id=str(payload["id"]),
        x=float(payload["x"]),
        y=float(payload["y"]),
        vx=float(payload.get("vx", 0)),
        vy=float(payload.get("vy", 0)),
        target=str(payload.get("target", "")),
        kind=str(payload.get("kind", "basic")),
        health=int(payload.get("health", 1)),
        speed=float(payload.get("speed", ENEMY_CONFIG.speed)),
        gain=int(payload.get("gain", ENEMY_CONFIG.gain)),
        target_age=float(payload.get("target_age", 0)),
    )


def player_payload(player: Player) -> dict[str, Any]:
    payload = asdict(player)
    now = time.monotonic()
    payload["color"] = list(player.color)
    payload["indicator_color"] = list(player.indicator_color)
    payload["invulnerable_remaining"] = max(0.0, player.invulnerable_until - now)
    payload["bullets"] = [bullet_payload(bullet) for bullet in player.bullets]
    return payload


def player_from_payload(payload: dict[str, Any]) -> Player:
    color = payload.get("color", [255, 255, 255])
    indicator_color = payload.get("indicator_color", color)
    return Player(
        name=str(payload["name"]),
        x=float(payload["x"]),
        y=float(payload["y"]),
        color=(int(color[0]), int(color[1]), int(color[2])),
        indicator_color=(
            int(indicator_color[0]),
            int(indicator_color[1]),
            int(indicator_color[2]),
        ),
        indicator_x=float(payload.get("indicator_x", payload["x"])),
        indicator_y=float(payload.get("indicator_y", payload["y"])),
        health=int(payload.get("health", HEALTH)),
        invulnerable_until=time.monotonic() + float(payload.get("invulnerable_remaining", 0)),
        respawn_at=float(payload.get("respawn_at", 0)),
        alive=bool(payload.get("alive", True)),
        bullets=[bullet_from_payload(item) for item in payload.get("bullets", [])],
    )


def copy_player_state(target: Player, source: Player) -> None:
    target.x = source.x
    target.y = source.y
    target.color = source.color
    target.indicator_color = source.indicator_color
    target.indicator_x = source.indicator_x
    target.indicator_y = source.indicator_y
    target.health = source.health
    target.invulnerable_until = source.invulnerable_until
    target.respawn_at = source.respawn_at
    target.alive = source.alive
    target.bullets = source.bullets
