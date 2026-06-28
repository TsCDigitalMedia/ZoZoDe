from __future__ import annotations

import random


def random_color() -> tuple[int, int, int]:
    return random.randint(80, 255), random.randint(80, 255), random.randint(80, 255)
