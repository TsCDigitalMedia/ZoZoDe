from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PlayerStatistics:
    magazine: int = 0
    health: int = 0
    score: int = 0
    rps_multiplier: float = 1.0
    damage_multiplier: float = 1.0


@dataclass(slots=True)
class Bullet:
    id: str
    owner: str
    x: float
    y: float
    vx: float
    vy: float
    damage: int = 1
    age: float = 0.0


@dataclass(slots=True)
class Enemy:
    id: str
    x: float
    y: float
    vx: float
    vy: float
    target: str
    kind: str = "basic"
    health: int = 1
    speed: float = 200.0
    damage: int = 1
    gain: int = 1
    target_age: float = 0.0
    path_next_update_at: float = 0.0
    path_target_x: float = 0.0
    path_target_y: float = 0.0


@dataclass(slots=True)
class Player:
    name: str
    x: float
    y: float
    color: tuple[int, int, int]
    indicator_color: tuple[int, int, int]
    indicator_x: float
    indicator_y: float
    health: int
    invulnerable_until: float = 0.0
    respawn_at: float = 0.0
    alive: bool = True
    bullets: list[Bullet] = field(default_factory=list)
    statistics: PlayerStatistics = field(default_factory=PlayerStatistics)
