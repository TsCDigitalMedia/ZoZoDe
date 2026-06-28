from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Player:
    name: str
    x: float
    y: float
    color: tuple[int, int, int]
    sword_color: tuple[int, int, int]
    sword_x: float
    sword_y: float
    health: int
    invulnerable_until: float = 0.0
    respawn_at: float = 0.0
    alive: bool = True
