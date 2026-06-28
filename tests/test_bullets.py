from zozode.bullets import maybe_spawn_bullet
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
    bullet = maybe_spawn_bullet(make_player(), (110, 100))

    assert bullet is not None
    assert bullet.owner == "player"


def test_maybe_spawn_bullet_blocks_dead_player():
    bullet = maybe_spawn_bullet(make_player(alive=False), (110, 100))

    assert bullet is None
