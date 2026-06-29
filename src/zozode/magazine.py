from __future__ import annotations

from dataclasses import dataclass

from zozode.assets import WeaponConfig


@dataclass(slots=True)
class MagazineState:
    weapon: WeaponConfig
    remaining: int | None = None
    reload_started_at: float = 0.0
    reload_duration: float | None = None

    def __post_init__(self) -> None:
        if self.remaining is None:
            self.remaining = self.weapon.magazine


def reset_magazine(magazine: MagazineState) -> None:
    magazine.remaining = magazine.weapon.magazine
    magazine.reload_started_at = 0.0
    magazine.reload_duration = None


def current_reload_duration(magazine: MagazineState) -> float:
    if magazine.reload_duration is not None:
        return magazine.reload_duration
    return magazine.weapon.reload_time


def reload_progress(magazine: MagazineState, now: float) -> float:
    if magazine.reload_started_at == 0:
        return 1.0
    duration = current_reload_duration(magazine)
    if duration <= 0:
        return 1.0
    return min(1.0, (now - magazine.reload_started_at) / duration)


def refresh_reload(magazine: MagazineState, now: float) -> None:
    if magazine.reload_started_at == 0:
        return
    if reload_progress(magazine, now) >= 1.0:
        magazine.remaining = magazine.weapon.magazine
        magazine.reload_started_at = 0.0
        magazine.reload_duration = None


def start_reload(magazine: MagazineState, now: float, duration: float | None = None) -> bool:
    refresh_reload(magazine, now)
    if magazine.reload_started_at != 0 or magazine.remaining == magazine.weapon.magazine:
        return False
    magazine.reload_started_at = now
    magazine.reload_duration = duration
    return True


def consume_magazine(magazine: MagazineState, now: float) -> bool:
    refresh_reload(magazine, now)
    if magazine.reload_started_at != 0:
        return False
    if magazine.remaining is None or magazine.remaining <= 0:
        start_reload(magazine, now)
        return False
    magazine.remaining -= 1
    if magazine.remaining == 0:
        start_reload(magazine, now)
    return True
