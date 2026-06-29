from __future__ import annotations

import heapq
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
            enemy.vx, enemy.vy = enemy_path_direction(enemy, target, level)
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


def enemy_path_direction(enemy: Enemy, target: Player, level: Level = DEFAULT_LEVEL) -> tuple[float, float]:
    waypoint = enemy_path_waypoint(enemy, target, level)
    return unit_vector(enemy.x, enemy.y, waypoint[0], waypoint[1])


def enemy_path_waypoint(
    enemy: Enemy,
    target: Player,
    level: Level = DEFAULT_LEVEL,
    cell_size: float = ENEMY_RADIUS * 2,
) -> tuple[float, float]:
    start = _grid_cell(enemy.x, enemy.y, cell_size)
    goal = _grid_cell(target.x, target.y, cell_size)
    if start == goal:
        return target.x, target.y

    path = _shortest_walkable_path(start, goal, level, cell_size)
    if len(path) >= 2:
        return _cell_center(path[1], cell_size, level)
    if path:
        return _cell_center(path[0], cell_size, level)
    return target.x, target.y


def _shortest_walkable_path(
    start: tuple[int, int],
    goal: tuple[int, int],
    level: Level,
    cell_size: float,
) -> list[tuple[int, int]]:
    frontier: list[tuple[float, tuple[int, int]]] = [(0.0, start)]
    came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    cost_so_far: dict[tuple[int, int], float] = {start: 0.0}

    while frontier:
        _, current = heapq.heappop(frontier)
        if current == goal:
            break
        for neighbor, step_cost in _walkable_neighbors(current, level, cell_size):
            new_cost = cost_so_far[current] + step_cost
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + _grid_distance(neighbor, goal)
                heapq.heappush(frontier, (priority, neighbor))
                came_from[neighbor] = current

    if goal not in came_from:
        return []

    path = [goal]
    current = goal
    while came_from[current] is not None:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def _walkable_neighbors(
    cell: tuple[int, int],
    level: Level,
    cell_size: float,
) -> list[tuple[tuple[int, int], float]]:
    neighbors = []
    for dx, dy, cost in (
        (-1, 0, 1.0),
        (1, 0, 1.0),
        (0, -1, 1.0),
        (0, 1, 1.0),
        (-1, -1, math.sqrt(2)),
        (-1, 1, math.sqrt(2)),
        (1, -1, math.sqrt(2)),
        (1, 1, math.sqrt(2)),
    ):
        neighbor = (cell[0] + dx, cell[1] + dy)
        if not _cell_in_bounds(neighbor, level, cell_size):
            continue
        x, y = _cell_center(neighbor, cell_size, level)
        if not level.can_walk(x, y, ENEMY_RADIUS):
            continue
        if dx and dy:
            side_x, side_y = _cell_center((cell[0] + dx, cell[1]), cell_size, level)
            other_x, other_y = _cell_center((cell[0], cell[1] + dy), cell_size, level)
            if not level.can_walk(side_x, side_y, ENEMY_RADIUS):
                continue
            if not level.can_walk(other_x, other_y, ENEMY_RADIUS):
                continue
        neighbors.append((neighbor, cost))
    return neighbors


def _grid_cell(x: float, y: float, cell_size: float) -> tuple[int, int]:
    return int(x // cell_size), int(y // cell_size)


def _cell_in_bounds(cell: tuple[int, int], level: Level, cell_size: float) -> bool:
    return 0 <= cell[0] <= int(level.width // cell_size) and 0 <= cell[1] <= int(level.height // cell_size)


def _cell_center(cell: tuple[int, int], cell_size: float, level: Level) -> tuple[float, float]:
    x = cell[0] * cell_size + cell_size / 2
    y = cell[1] * cell_size + cell_size / 2
    return min(max(x, ENEMY_RADIUS), level.width - ENEMY_RADIUS), min(
        max(y, ENEMY_RADIUS),
        level.height - ENEMY_RADIUS,
    )


def _grid_distance(start: tuple[int, int], goal: tuple[int, int]) -> float:
    return math.hypot(goal[0] - start[0], goal[1] - start[1])


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
