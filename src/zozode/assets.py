from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _asset_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "assets"
    return Path(__file__).resolve().parents[2] / "assets"


ASSETS_DIR = _asset_root()


@dataclass(frozen=True, slots=True)
class WeaponConfig:
    name: str
    rps: float
    magazine: int
    reload_time: float
    spread: float
    is_holdable: bool

    @property
    def shot_interval_seconds(self) -> float:
        return 1 / self.rps


@dataclass(frozen=True, slots=True)
class EnemyConfig:
    health: int
    speed: float
    size: int


def load_json_asset(filename: str) -> dict[str, Any]:
    with (ASSETS_DIR / filename).open(encoding="utf-8") as file:
        return json.load(file)


def load_default_weapon() -> WeaponConfig:
    payload = load_json_asset("weapons.json")
    default_name = str(payload["default_weapon"])
    weapon_payload = payload[default_name.lower()]
    return WeaponConfig(
        name=str(weapon_payload.get("name", default_name)),
        rps=float(weapon_payload["rps"]),
        magazine=int(weapon_payload["magazine"]),
        reload_time=float(weapon_payload.get("reloadTime", 1.5)),
        spread=float(weapon_payload.get("spread", 0)),
        is_holdable=bool(weapon_payload.get("isHoldable", False)),
    )


def load_basic_enemy() -> EnemyConfig:
    payload = load_json_asset("enemy.json")["basic"]
    return EnemyConfig(
        health=int(payload.get("health", 1)),
        speed=float(payload.get("speed", 200)),
        size=int(payload.get("size", 20)),
    )
