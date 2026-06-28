from zozode.assets import WeaponConfig
from zozode.bullets import maybe_spawn_bullet, spawn_bullet
from zozode.player import Player

TEST_WEAPON = WeaponConfig(name="Test", rps=5, ammo=10, spread=0, is_holdable=False)


def make_player(alive: bool = True) -> Player:
    return Player(
        name="player",
        x=100,
        y=100,
        color=(255, 255, 255),
        indicator_color=(255, 255, 255),
        indicator_x=100,
        indicator_y=100,
        health=3,
        alive=alive,
    )


def test_maybe_spawn_bullet_returns_bullet_for_alive_player():
    bullet, next_shot_at = maybe_spawn_bullet(make_player(), (110, 100), 10.0, 0.0, TEST_WEAPON)

    assert bullet is not None
    assert bullet.owner == "player"
    assert next_shot_at == 10.0 + TEST_WEAPON.shot_interval_seconds


def test_maybe_spawn_bullet_blocks_dead_player():
    bullet, next_shot_at = maybe_spawn_bullet(
        make_player(alive=False),
        (110, 100),
        10.0,
        0.0,
        TEST_WEAPON,
    )

    assert bullet is None
    assert next_shot_at == 0.0


def test_maybe_spawn_bullet_respects_rounds_per_second():
    bullet, next_shot_at = maybe_spawn_bullet(make_player(), (110, 100), 10.0, 10.1, TEST_WEAPON)

    assert bullet is None
    assert next_shot_at == 10.1


def test_spawn_bullet_applies_weapon_spread(monkeypatch):
    weapon = WeaponConfig(name="Spread", rps=5, ammo=10, spread=0.5, is_holdable=False)
    monkeypatch.setattr("zozode.bullets.random.uniform", lambda _low, _high: 0.5)

    bullet = spawn_bullet(make_player(), (110, 100), weapon)

    assert round(bullet.vx, 6) == round(420 * 0.8775825618903728, 6)
    assert round(bullet.vy, 6) == round(420 * 0.479425538604203, 6)
