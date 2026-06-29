from zozode.enemies import PATH_RECOMPUTE_SECONDS, enemy_path_waypoint, player_predictions, step_enemies
from zozode.level import Level, LevelShape
from zozode.player import Enemy, Player
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
    level = Level(
        width=120,
        height=120,
        ground=(LevelShape(kind="rect", x=0, y=0, width=120, height=120),),
        enemy_spawns=(LevelShape(kind="rect", x=10, y=10, width=0, height=0),),
        player_spawns=(),
    )
    players = {
        "near": make_player("near", 10, 20),
        "far": make_player("far", 700, 500),
    }

    enemy = spawn_enemy(players, level=level)

    assert enemy is not None
    assert enemy.target == "near"


def test_spawn_enemy_randomly_selects_between_equally_nearest_players(monkeypatch):
    monkeypatch.setattr("zozode.player_state.random.randrange", lambda _limit: 0)
    selected = []
    level = Level(
        width=120,
        height=120,
        ground=(LevelShape(kind="rect", x=0, y=0, width=120, height=120),),
        enemy_spawns=(LevelShape(kind="rect", x=10, y=20, width=0, height=0),),
        player_spawns=(),
    )

    def choose(items):
        selected.append([item.name for item in items])
        return items[-1]

    monkeypatch.setattr("zozode.player_state.random.choice", choose)
    players = {
        "left": make_player("left", 0, 20),
        "right": make_player("right", 20, 20),
        "far": make_player("far", 700, 500),
    }

    enemy = spawn_enemy(players, level=level)

    assert enemy is not None
    assert selected[-1] == ["left", "right"]
    assert enemy.target == "right"


def test_enemy_default_size_matches_player_size():
    from zozode.constants import DOT_RADIUS, ENEMY_RADIUS

    assert ENEMY_RADIUS == DOT_RADIUS


def test_enemy_defaults_to_one_health(monkeypatch):
    monkeypatch.setattr("zozode.player_state.random.randrange", lambda _limit: 0)
    level = Level(
        width=120,
        height=120,
        ground=(LevelShape(kind="rect", x=0, y=0, width=120, height=120),),
        enemy_spawns=(LevelShape(kind="rect", x=10, y=10, width=0, height=0),),
        player_spawns=(),
    )
    players = {"near": make_player("near", 10, 20)}

    enemy = spawn_enemy(players, level=level)

    assert enemy is not None
    assert enemy.health == 1


def test_enemy_is_killed_by_one_bullet():
    from zozode.bullets import spawn_bullet
    from zozode.enemies import handle_enemy_hits

    player = make_player("player", 100, 100)
    enemy = Enemy(id="enemy", x=100, y=100, vx=0, vy=0, target="player")
    player.bullets.append(spawn_bullet(player, (110, 100)))
    players = {player.name: player}
    enemies = [enemy]

    handle_enemy_hits(enemies, players)

    assert enemies == []
    assert player.bullets == []


def test_weapon_damage_reduces_enemy_health():
    from zozode.enemies import handle_enemy_hits
    from zozode.player import Bullet

    player = make_player("player", 100, 100)
    enemy = Enemy(id="enemy", x=100, y=100, vx=0, vy=0, target="player", health=3)
    player.bullets.append(Bullet(id="bullet", owner="player", x=100, y=100, vx=0, vy=0, damage=2))
    players = {player.name: player}
    enemies = [enemy]

    handle_enemy_hits(enemies, players)

    assert enemies == [enemy]
    assert enemy.health == 1
    assert player.bullets == []


def test_enemy_path_waypoint_goes_direct_when_target_is_visible():
    level = Level(
        width=140,
        height=140,
        ground=(LevelShape(kind="rect", x=0, y=0, width=140, height=140),),
        enemy_spawns=(),
        player_spawns=(),
    )
    enemy = Enemy(id="enemy", x=20, y=20, vx=0, vy=0, target="player")
    player = make_player("player", 120, 80)

    waypoint = enemy_path_waypoint(enemy, player, level, cell_size=20)

    assert waypoint == (player.x, player.y)


def test_enemy_path_waypoint_routes_around_obstacle():
    level = Level(
        width=140,
        height=140,
        ground=(LevelShape(kind="rect", x=0, y=0, width=140, height=140),),
        enemy_spawns=(),
        player_spawns=(),
        obstacles=(LevelShape(kind="rect", x=40, y=0, width=20, height=100),),
    )
    enemy = Enemy(id="enemy", x=20, y=20, vx=0, vy=0, target="player")
    player = make_player("player", 120, 20)

    waypoint = enemy_path_waypoint(enemy, player, level, cell_size=20)

    assert waypoint != (player.x, player.y)
    assert level.can_walk(*waypoint, 10)
    assert waypoint[1] > enemy.y


def test_step_enemies_walks_around_obstacle():
    level = Level(
        width=140,
        height=140,
        ground=(LevelShape(kind="rect", x=0, y=0, width=140, height=140),),
        enemy_spawns=(),
        player_spawns=(),
        obstacles=(LevelShape(kind="rect", x=40, y=0, width=20, height=100),),
    )
    enemy = Enemy(id="enemy", x=20, y=20, vx=0, vy=0, target="player", speed=20)
    player = make_player("player", 120, 20)
    enemies = [enemy]

    step_enemies(enemies, {player.name: player}, 1.0, 0.0, 0, level)

    assert enemies == [enemy]
    assert enemy.y > 20
    assert enemy.x < 40
    assert level.can_walk(enemy.x, enemy.y, 10)


def test_step_enemies_reuses_path_map_for_shared_target(monkeypatch):
    import zozode.enemies as enemy_module

    level = Level(
        width=140,
        height=140,
        ground=(LevelShape(kind="rect", x=0, y=0, width=140, height=140),),
        enemy_spawns=(),
        player_spawns=(),
        obstacles=(LevelShape(kind="rect", x=40, y=0, width=20, height=100),),
    )
    player = make_player("player", 120, 20)
    enemies = [
        Enemy(id="enemy-a", x=20, y=20, vx=0, vy=0, target="player", speed=20),
        Enemy(id="enemy-b", x=20, y=40, vx=0, vy=0, target="player", speed=20),
    ]
    calls = 0
    original = enemy_module._walkable_costs_to_goal

    def counting_walkable_costs_to_goal(goal, level, cell_size):
        nonlocal calls
        calls += 1
        return original(goal, level, cell_size)

    monkeypatch.setattr(enemy_module, "_walkable_costs_to_goal", counting_walkable_costs_to_goal)

    step_enemies(enemies, {player.name: player}, 1.0, 0.0, 0, level)

    assert calls == 1
    assert len(enemies) == 2


def test_player_predictions_uses_player_motion_vector(monkeypatch):
    import zozode.enemies as enemy_module

    enemy_module._PLAYER_TRACKS.clear()
    level = Level(
        width=200,
        height=200,
        ground=(LevelShape(kind="rect", x=0, y=0, width=200, height=200),),
        enemy_spawns=(),
        player_spawns=(),
    )
    player = make_player("player", 50, 50)

    assert player_predictions({player.name: player}, 1.0, level)[player.name] == (50, 50)
    player.x = 70

    assert player_predictions({player.name: player}, 2.0, level)[player.name] == (80, 50)


def test_step_enemies_recomputes_path_every_500ms(monkeypatch):
    import zozode.enemies as enemy_module

    enemy_module._PLAYER_TRACKS.clear()
    level = Level(
        width=200,
        height=200,
        ground=(LevelShape(kind="rect", x=0, y=0, width=200, height=200),),
        enemy_spawns=(),
        player_spawns=(),
    )
    player = make_player("player", 120, 20)
    enemy = Enemy(id="enemy", x=20, y=20, vx=0, vy=0, target="player", speed=0)

    step_enemies([enemy], {player.name: player}, 0.1, 1.0, 0, level)
    first_vx = enemy.vx
    player.x = 20
    player.y = 120
    step_enemies([enemy], {player.name: player}, 0.1, 1.0 + PATH_RECOMPUTE_SECONDS / 2, 0, level)

    assert enemy.vx == first_vx

    step_enemies([enemy], {player.name: player}, 0.1, 1.0 + PATH_RECOMPUTE_SECONDS, 0, level)

    assert enemy.vy > 0
