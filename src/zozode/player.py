from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Player:
    name: str
    x: float
    y: float
    color: tuple[int, int, int]
