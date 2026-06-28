from zozode.bullets import maybe_spawn_bullet
from zozode.constants import SHOT_INTERVAL_SECONDS
from zozode.player import Player


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
    bullet, next_shot_at = maybe_spawn_bullet(make_player(), (110, 100), 10.0, 0.0)

    assert bullet is not None
    assert bullet.owner == "player"
    assert next_shot_at == 10.0 + SHOT_INTERVAL_SECONDS


def test_maybe_spawn_bullet_blocks_dead_player():
    bullet, next_shot_at = maybe_spawn_bullet(make_player(alive=False), (110, 100), 10.0, 0.0)

    assert bullet is None
    assert next_shot_at == 0.0


def test_maybe_spawn_bullet_respects_rounds_per_second():
    bullet, next_shot_at = maybe_spawn_bullet(make_player(), (110, 100), 10.0, 10.1)

    assert bullet is None
    assert next_shot_at == 10.1
