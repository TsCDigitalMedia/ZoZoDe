from zozode.combat import damage_player, respawn_dead_players
from zozode.constants import HEALTH, RESPAWN_SECONDS
from zozode.level import Level, LevelShape
from zozode.player import Bullet, Player


def make_player() -> Player:
    return Player(
        name="player",
        x=20,
        y=20,
        color=(255, 255, 255),
        indicator_color=(255, 255, 255),
        indicator_x=20,
        indicator_y=20,
        health=HEALTH,
    )


def test_damage_player_resets_stats_on_death():
    player = make_player()
    player.health = 1
    player.invulnerable_until = 99.0
    player.bullets.append(Bullet(id="bullet", owner="player", x=20, y=20, vx=1, vy=0))

    damage_player(player, 10.0)

    assert not player.alive
    assert player.health == HEALTH
    assert player.respawn_at == 10.0 + RESPAWN_SECONDS
    assert player.invulnerable_until == 0
    assert player.bullets == []


def test_damage_player_keeps_damaged_stats_when_player_survives():
    player = make_player()

    damage_player(player, 10.0)

    assert player.alive
    assert player.health == HEALTH - 1
    assert player.respawn_at == 0
    assert player.invulnerable_until > 10.0


def test_respawn_dead_players_keeps_default_stats_after_respawn():
    level = Level(
        width=100,
        height=100,
        ground=(LevelShape(kind="rect", x=0, y=0, width=100, height=100),),
        enemy_spawns=(),
        player_spawns=(LevelShape(kind="rect", x=30, y=40, width=0, height=0),),
    )
    player = make_player()
    player.alive = False
    player.health = 1
    player.respawn_at = 10.0
    player.invulnerable_until = 99.0
    player.bullets.append(Bullet(id="bullet", owner="player", x=20, y=20, vx=1, vy=0))

    respawn_dead_players({player.name: player}, 10.0, level)

    assert player.alive
    assert player.health == HEALTH
    assert player.respawn_at == 0
    assert player.invulnerable_until == 0
    assert player.bullets == []
    assert (player.x, player.y) == (30, 40)
