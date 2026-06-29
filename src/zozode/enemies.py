from __future__ import annotations

import math
import random

from zozode.assets import load_enemy_configs
from zozode.combat import damage_player
from zozode.constants import (
    BULLET_RADIUS,
    DIFFICULTY_EASY,
    ENEMY_BASE_SPAWN_SECONDS,
    ENEMY_RADIUS,
    ENEMY_SPAWN_SPEED_STEP,
    ENEMY_SPEED_STEP,
    ENEMY_TARGET_SECONDS,
)
from zozode.geometry import unit_vector
from zozode.level import DEFAULT_LEVEL, Level
from zozode.player import Enemy, Player
from zozode.player_state import spawn_enemy

ENEMY_CONFIGS = load_enemy_configs()


def enemy_speed(enemy: Enemy, difficulty: int) -> float:
    return enemy.speed * (1 + max(DIFFICULTY_EASY, difficulty) * ENEMY_SPEED_STEP)


def enemy_spawn_count(chance: float) -> int:
    guaranteed = max(0, int(chance))
    remainder = max(0.0, chance - guaranteed)
    if random.random() < remainder:
        return guaranteed + 1
    return guaranteed


def enemy_spawn_seconds(difficulty: int) -> float:
    spawn_rate = 1 + max(DIFFICULTY_EASY, difficulty) * ENEMY_SPAWN_SPEED_STEP
    return ENEMY_BASE_SPAWN_SECONDS / spawn_rate


def maybe_spawn_enemy(
    enemies: list[Enemy],
    players: dict[str, Player],
    now: float,
    next_spawn_at: float,
    difficulty: int,
    level: Level = DEFAULT_LEVEL,
) -> float:
    if now < next_spawn_at:
        return next_spawn_at
    for kind, config in ENEMY_CONFIGS.items():
        for _ in range(enemy_spawn_count(config.chance)):
            enemy = spawn_enemy(players, config, kind, level)
            if enemy is not None:
                enemies.append(enemy)
    return now + enemy_spawn_seconds(difficulty)


def handle_enemy_hits(enemies: list[Enemy], players: dict[str, Player]) -> int:
    score_gain = 0
    active_enemies = []
    for enemy in enemies:
        if bullet_hits_enemy(enemy, players):
            enemy.health = max(0, enemy.health - 1)
        if enemy.health > 0:
            active_enemies.append(enemy)
        else:
            score_gain += enemy.gain
    enemies[:] = active_enemies
    return score_gain


def bullet_hits_enemy(enemy: Enemy, players: dict[str, Player]) -> bool:
    for player in players.values():
        active_bullets = []
        hit = False
        for bullet in player.bullets:
            distance = math.hypot(enemy.x - bullet.x, enemy.y - bullet.y)
            if not hit and distance <= ENEMY_RADIUS + BULLET_RADIUS:
                hit = True
                continue
            active_bullets.append(bullet)
        player.bullets = active_bullets
        if hit:
            return True
    return False


def step_enemies(
    enemies: list[Enemy],
    players: dict[str, Player],
    dt: float,
    now: float,
    difficulty: int,
    level: Level = DEFAULT_LEVEL,
) -> None:
    active = []
    for enemy in enemies:
        speed = enemy_speed(enemy, difficulty)
        enemy.target_age += dt
        target = players.get(enemy.target)
        if target is None or not target.alive or enemy.target_age >= ENEMY_TARGET_SECONDS:
            target = choose_target(enemy, players)
            if target is not None:
                enemy.target = target.name
                enemy.target_age = 0
        if target is not None:
            enemy.vx, enemy.vy = unit_vector(enemy.x, enemy.y, target.x, target.y)
        move_enemy_on_ground(enemy, speed * dt, level)
        if hit_player(enemy, players, now):
            continue
        if level.in_bounds(enemy.x, enemy.y, ENEMY_RADIUS * 2) and level.can_walk(
            enemy.x,
            enemy.y,
            ENEMY_RADIUS,
        ):
            active.append(enemy)
    enemies[:] = active


def move_enemy_on_ground(enemy: Enemy, distance: float, level: Level = DEFAULT_LEVEL) -> None:
    x = enemy.x + enemy.vx * distance
    y = enemy.y + enemy.vy * distance
    if level.can_walk(x, y, ENEMY_RADIUS):
        enemy.x = x
        enemy.y = y
    elif level.can_walk(x, enemy.y, ENEMY_RADIUS):
        enemy.x = x
        enemy.vy = 0
    elif level.can_walk(enemy.x, y, ENEMY_RADIUS):
        enemy.y = y
        enemy.vx = 0
    else:
        enemy.vx = 0
        enemy.vy = 0


def choose_target(enemy: Enemy, players: dict[str, Player]) -> Player | None:
    alive = [player for player in players.values() if player.alive]
    if not alive:
        return None
    nearest_distance = min(math.hypot(player.x - enemy.x, player.y - enemy.y) for player in alive)
    nearest = [
        player
        for player in alive
        if math.hypot(player.x - enemy.x, player.y - enemy.y) == nearest_distance
    ]
    return random.choice(nearest)


def hit_player(enemy: Enemy, players: dict[str, Player], now: float) -> bool:
    for player in players.values():
        if not player.alive or player.invulnerable_until > now:
            continue
        distance = math.hypot(player.x - enemy.x, player.y - enemy.y)
        if distance <= ENEMY_RADIUS + 10:
            damage_player(player, now, enemy.damage)
            return True
    return False
