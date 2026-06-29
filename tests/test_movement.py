from zozode.level import Level, LevelShape
from zozode.movement import move_player_on_ground
from zozode.player import Player


def make_player(x: float, y: float) -> Player:
    return Player(
        name="player",
        x=x,
        y=y,
        color=(255, 255, 255),
        indicator_color=(255, 255, 255),
        indicator_x=x,
        indicator_y=y,
        health=3,
    )


def test_move_player_does_not_enter_missing_ground():
    level = Level(
        width=120,
        height=120,
        ground=(LevelShape(kind="rect", x=20, y=20, width=80, height=80),),
        enemy_spawns=(),
        player_spawns=(),
    )
    player = make_player(50, 50)

    move_player_on_ground(player, 10, 50, level)

    assert player.x == 50
    assert player.y == 50


def test_move_player_slides_along_missing_ground_edge():
    level = Level(
        width=120,
        height=120,
        ground=(LevelShape(kind="rect", x=20, y=20, width=80, height=80),),
        enemy_spawns=(),
        player_spawns=(),
    )
    player = make_player(50, 50)

    move_player_on_ground(player, 10, 60, level)

    assert player.x == 50
    assert player.y == 60


def test_move_player_does_not_snap_to_level_edge():
    level = Level(
        width=120,
        height=120,
        ground=(LevelShape(kind="rect", x=0, y=0, width=120, height=120),),
        enemy_spawns=(),
        player_spawns=(),
    )
    player = make_player(15, 50)

    move_player_on_ground(player, -20, 50, level)

    assert player.x == 15
    assert player.y == 50


def test_move_player_slides_along_level_edge_without_snap():
    level = Level(
        width=120,
        height=120,
        ground=(LevelShape(kind="rect", x=0, y=0, width=120, height=120),),
        enemy_spawns=(),
        player_spawns=(),
    )
    player = make_player(15, 50)

    move_player_on_ground(player, -20, 60, level)

    assert player.x == 15
    assert player.y == 60


def test_move_player_slides_smoothly_on_large_blocked_step():
    level = Level(
        width=120,
        height=120,
        ground=(LevelShape(kind="rect", x=20, y=20, width=80, height=80),),
        enemy_spawns=(),
        player_spawns=(),
    )
    player = make_player(50, 50)

    move_player_on_ground(player, 10, 90, level)

    assert player.x == 50
    assert player.y == 90


def test_move_player_slides_along_top_ground_edge_with_radius_clearance():
    level = Level(
        width=120,
        height=120,
        ground=(LevelShape(kind="rect", x=20, y=20, width=80, height=80),),
        enemy_spawns=(),
        player_spawns=(),
    )
    player = make_player(50, 30)

    move_player_on_ground(player, 60, 15, level)

    assert player.x == 60
    assert player.y == 30
