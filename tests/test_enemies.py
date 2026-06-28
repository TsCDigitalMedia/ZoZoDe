from zozode.player import Player
from zozode.player_state import spawn_enemy


def make_player(name: str, x: float, y: float) -> Player:
    return Player(
        name=name,
        x=x,
        y=y,
        color=(255, 255, 255),
        indicator_color=(255, 255, 255),
        indicator_x=x,
        indicator_y=y,
        health=3,
    )


def test_spawn_enemy_targets_random_nearest_alive_player(monkeypatch):
    monkeypatch.setattr("zozode.player_state.random.randrange", lambda _limit: 0)
    monkeypatch.setattr("zozode.player_state.random.uniform", lambda _low, _high: 10)

    players = {
        "near": make_player("near", 10, 20),
        "far": make_player("far", 700, 500),
    }

    enemy = spawn_enemy(players)

    assert enemy is not None
    assert enemy.target == "near"


def test_spawn_enemy_randomly_selects_between_equally_nearest_players(monkeypatch):
    monkeypatch.setattr("zozode.player_state.random.randrange", lambda _limit: 0)
    monkeypatch.setattr("zozode.player_state.random.uniform", lambda _low, _high: 10)
    selected = []

    def choose(items):
        selected.append([item.name for item in items])
        return items[-1]

    monkeypatch.setattr("zozode.player_state.random.choice", choose)
    players = {
        "left": make_player("left", 0, 20),
        "right": make_player("right", 20, 20),
        "far": make_player("far", 700, 500),
    }

    enemy = spawn_enemy(players)

    assert enemy is not None
    assert selected[-1] == ["left", "right"]
    assert enemy.target == "right"


def test_enemy_default_size_matches_player_size():
    from zozode.constants import DOT_RADIUS, ENEMY_RADIUS

    assert ENEMY_RADIUS == DOT_RADIUS


def test_enemy_defaults_to_one_health(monkeypatch):
    monkeypatch.setattr("zozode.player_state.random.randrange", lambda _limit: 0)
    monkeypatch.setattr("zozode.player_state.random.uniform", lambda _low, _high: 10)
    players = {"near": make_player("near", 10, 20)}

    enemy = spawn_enemy(players)

    assert enemy is not None
    assert enemy.health == 1


def test_enemy_is_killed_by_one_bullet():
    from zozode.bullets import spawn_bullet
    from zozode.enemies import handle_enemy_hits
    from zozode.player import Enemy

    player = make_player("player", 100, 100)
    enemy = Enemy(id="enemy", x=100, y=100, vx=0, vy=0, target="player")
    player.bullets.append(spawn_bullet(player, (110, 100)))
    players = {player.name: player}
    enemies = [enemy]

    handle_enemy_hits(enemies, players)

    assert enemies == []
    assert player.bullets == []
