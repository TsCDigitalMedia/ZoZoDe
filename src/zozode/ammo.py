from __future__ import annotations

from dataclasses import dataclass

from zozode.assets import WeaponConfig


@dataclass(slots=True)
class AmmoState:
    weapon: WeaponConfig
    remaining: int | None = None
    reload_started_at: float = 0.0
    reload_duration: float | None = None

    def __post_init__(self) -> None:
        if self.remaining is None:
            self.remaining = self.weapon.ammo


def current_reload_duration(ammo: AmmoState) -> float:
    if ammo.reload_duration is not None:
        return ammo.reload_duration
    return ammo.weapon.reload_time


def reload_progress(ammo: AmmoState, now: float) -> float:
    if ammo.reload_started_at == 0:
        return 1.0
    duration = current_reload_duration(ammo)
    if duration <= 0:
        return 1.0
    return min(1.0, (now - ammo.reload_started_at) / duration)


def refresh_reload(ammo: AmmoState, now: float) -> None:
    if ammo.reload_started_at == 0:
        return
    if reload_progress(ammo, now) >= 1.0:
        ammo.remaining = ammo.weapon.ammo
        ammo.reload_started_at = 0.0
        ammo.reload_duration = None


def start_reload(ammo: AmmoState, now: float, duration: float | None = None) -> bool:
    refresh_reload(ammo, now)
    if ammo.reload_started_at != 0 or ammo.remaining == ammo.weapon.ammo:
        return False
    ammo.reload_started_at = now
    ammo.reload_duration = duration
    return True


def consume_ammo(ammo: AmmoState, now: float) -> bool:
    refresh_reload(ammo, now)
    if ammo.reload_started_at != 0:
        return False
    if ammo.remaining is None or ammo.remaining <= 0:
        start_reload(ammo, now)
        return False
    ammo.remaining -= 1
    if ammo.remaining == 0:
        start_reload(ammo, now)
    return True
