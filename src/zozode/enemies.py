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
PATH_RECOMPUTE_SECONDS = 0.5
TARGET_PREDICTION_SECONDS = 0.5
_PLAYER_TRACKS: dict[str, tuple[float, float, float, float, float]] = {}


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
    predictions = player_predictions(players, now, level)
    path_maps: dict[tuple[int, int], dict[tuple[int, int], float]] = {}
    for enemy in enemies:
        speed = enemy_speed(enemy, difficulty)
        enemy.target_age += dt
        target = players.get(enemy.target)
        if target is None or not target.alive or enemy.target_age >= ENEMY_TARGET_SECONDS:
            target = choose_target(enemy, players)
            if target is not None:
                enemy.target = target.name
                enemy.target_age = 0
                enemy.path_next_update_at = 0
        if target is not None and now >= enemy.path_next_update_at:
            target_x, target_y = predictions[target.name]
            enemy.vx, enemy.vy = enemy_path_direction_to(enemy, target_x, target_y, level, path_maps)
            enemy.path_target_x = target_x
            enemy.path_target_y = target_y
            enemy.path_next_update_at = now + PATH_RECOMPUTE_SECONDS
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


def player_predictions(
    players: dict[str, Player],
    now: float,
    level: Level = DEFAULT_LEVEL,
) -> dict[str, tuple[float, float]]:
    predictions: dict[str, tuple[float, float]] = {}
    live_names = set(players)
    for stale_name in list(_PLAYER_TRACKS):
        if stale_name not in live_names:
            _PLAYER_TRACKS.pop(stale_name, None)

    for name, player in players.items():
        previous = _PLAYER_TRACKS.get(name)
        if previous is None:
            vx = 0.0
            vy = 0.0
        else:
            previous_x, previous_y, previous_time, previous_vx, previous_vy = previous
            elapsed = max(0.0, now - previous_time)
            if elapsed > 0:
                vx = (player.x - previous_x) / elapsed
                vy = (player.y - previous_y) / elapsed
            else:
                vx = previous_vx
                vy = previous_vy

        predicted_x = min(max(player.x + vx * TARGET_PREDICTION_SECONDS, ENEMY_RADIUS), level.width - ENEMY_RADIUS)
        predicted_y = min(max(player.y + vy * TARGET_PREDICTION_SECONDS, ENEMY_RADIUS), level.height - ENEMY_RADIUS)
        if not level.can_walk(predicted_x, predicted_y, ENEMY_RADIUS):
            predicted_x = player.x
            predicted_y = player.y
        predictions[name] = (predicted_x, predicted_y)
        _PLAYER_TRACKS[name] = (player.x, player.y, now, vx, vy)
    return predictions


def enemy_path_direction(
    enemy: Enemy,
    target: Player,
    level: Level = DEFAULT_LEVEL,
    path_maps: dict[tuple[int, int], dict[tuple[int, int], float]] | None = None,
) -> tuple[float, float]:
    return enemy_path_direction_to(enemy, target.x, target.y, level, path_maps)


def enemy_path_direction_to(
    enemy: Enemy,
    target_x: float,
    target_y: float,
    level: Level = DEFAULT_LEVEL,
    path_maps: dict[tuple[int, int], dict[tuple[int, int], float]] | None = None,
) -> tuple[float, float]:
    waypoint = enemy_path_waypoint_to(enemy, target_x, target_y, level, path_maps=path_maps)
    return unit_vector(enemy.x, enemy.y, waypoint[0], waypoint[1])


def enemy_path_waypoint(
    enemy: Enemy,
    target: Player,
    level: Level = DEFAULT_LEVEL,
    cell_size: float = ENEMY_RADIUS * 2,
    path_maps: dict[tuple[int, int], dict[tuple[int, int], float]] | None = None,
) -> tuple[float, float]:
    return enemy_path_waypoint_to(enemy, target.x, target.y, level, cell_size, path_maps)


def enemy_path_waypoint_to(
    enemy: Enemy,
    target_x: float,
    target_y: float,
    level: Level = DEFAULT_LEVEL,
    cell_size: float = ENEMY_RADIUS * 2,
    path_maps: dict[tuple[int, int], dict[tuple[int, int], float]] | None = None,
) -> tuple[float, float]:
    if _direct_path_clear(enemy.x, enemy.y, target_x, target_y, level, cell_size):
        return target_x, target_y

    start = _grid_cell(enemy.x, enemy.y, cell_size)
    goal = _grid_cell(target_x, target_y, cell_size)
    if start == goal:
        return target_x, target_y

    if path_maps is None:
        path_costs = _walkable_costs_to_goal(goal, level, cell_size)
    else:
        path_costs = path_maps.get(goal)
        if path_costs is None:
            path_costs = _walkable_costs_to_goal(goal, level, cell_size)
            path_maps[goal] = path_costs

    path = _greedy_walkable_path(start, goal, path_costs, level, cell_size)
    for cell in reversed(path[1:]):
        x, y = _cell_center(cell, cell_size, level)
        if _direct_path_clear(enemy.x, enemy.y, x, y, level, cell_size):
            return x, y
    if path:
        return _cell_center(path[0], cell_size, level)
    return target_x, target_y


def _direct_path_clear(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    level: Level,
    cell_size: float,
) -> bool:
    distance = math.hypot(end_x - start_x, end_y - start_y)
    steps = max(1, int(distance / (cell_size / 2)))
    for step in range(1, steps + 1):
        amount = step / steps
        x = start_x + (end_x - start_x) * amount
        y = start_y + (end_y - start_y) * amount
        if not level.can_walk(x, y, ENEMY_RADIUS):
            return False
    return True


def _walkable_costs_to_goal(
    goal: tuple[int, int],
    level: Level,
    cell_size: float,
) -> dict[tuple[int, int], float]:
    frontier: list[tuple[float, tuple[int, int]]] = [(0.0, goal)]
    cost_so_far: dict[tuple[int, int], float] = {goal: 0.0}

    while frontier:
        _, current = heapq.heappop(frontier)
        for neighbor, step_cost in _walkable_neighbors(current, level, cell_size):
            new_cost = cost_so_far[current] + step_cost
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                heapq.heappush(frontier, (new_cost, neighbor))

    return cost_so_far


def _greedy_walkable_path(
    start: tuple[int, int],
    goal: tuple[int, int],
    path_costs: dict[tuple[int, int], float],
    level: Level,
    cell_size: float,
) -> list[tuple[int, int]]:
    if start not in path_costs:
        return []

    path = [start]
    current = start
    visited = {start}
    while current != goal:
        current_cost = path_costs[current]
        candidates = [
            (path_costs[neighbor], step_cost, neighbor)
            for neighbor, step_cost in _walkable_neighbors(current, level, cell_size)
            if neighbor in path_costs and neighbor not in visited and path_costs[neighbor] < current_cost
        ]
        if not candidates:
            break
        _, _, current = min(candidates)
        path.append(current)
        visited.add(current)
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
    x = cell[0] * cell_size
    y = cell[1] * cell_size
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
