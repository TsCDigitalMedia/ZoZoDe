from zozode.assets import WeaponConfig
from zozode.bullets import shot_interval_seconds, spawn_bullet
from zozode.magazine import DEFAULT_AMMO, MagazineState
from zozode.player import Player
from zozode.powerups import apply_powerup

TEST_WEAPON = WeaponConfig(
    name="Test",
    rps=5,
    magazine=10,
    reload_time=1.5,
    spread=0,
    damage=2,
    is_holdable=False,
)


def make_player(score: int = 0) -> Player:
    player = Player(
        name="player",
        x=0,
        y=0,
        color=(255, 255, 255),
        indicator_color=(255, 255, 255),
        indicator_x=0,
        indicator_y=0,
        health=3,
    )
    player.statistics.score = score
    player.statistics.health = player.health
    return player


def test_rps_powerup_decreases_own_score_and_multiplies_shot_rate():
    player = make_player(30)
    magazine = MagazineState(TEST_WEAPON)

    assert apply_powerup(player, magazine, "rps")

    assert player.statistics.score == 0
    assert player.statistics.rps_multiplier == 2.0
    assert shot_interval_seconds(player, TEST_WEAPON) == 1 / 10


def test_health_powerup_decreases_own_score_and_multiplies_health():
    player = make_player(60)
    magazine = MagazineState(TEST_WEAPON)

    assert apply_powerup(player, magazine, "health")

    assert player.statistics.score == 0
    assert player.health == 6
    assert player.statistics.health == 6


def test_damage_powerup_decreases_own_score_and_multiplies_bullet_damage():
    player = make_player(90)
    magazine = MagazineState(TEST_WEAPON)

    assert apply_powerup(player, magazine, "damage")
    bullet = spawn_bullet(player, (10, 0), TEST_WEAPON)

    assert player.statistics.score == 0
    assert player.statistics.damage_multiplier == 2.0
    assert bullet.damage == 4


def test_refill_ammo_decreases_own_score_and_refills_ammo():
    player = make_player(10)
    magazine = MagazineState(TEST_WEAPON, ammo=1)

    assert apply_powerup(player, magazine, "ammo")

    assert player.statistics.score == 0
    assert magazine.ammo == DEFAULT_AMMO


def test_powerup_does_nothing_when_own_score_is_too_low():
    player = make_player(29)
    magazine = MagazineState(TEST_WEAPON, ammo=1)

    assert not apply_powerup(player, magazine, "rps")

    assert player.statistics.score == 29
    assert player.statistics.rps_multiplier == 1.0
    assert magazine.ammo == 1


def test_powerup_only_changes_selected_player():
    buyer = make_player(90)
    other = make_player(90)
    buyer_magazine = MagazineState(TEST_WEAPON)

    assert apply_powerup(buyer, buyer_magazine, "damage")

    assert buyer.statistics.score == 0
    assert buyer.statistics.damage_multiplier == 2.0
    assert other.statistics.score == 90
    assert other.statistics.damage_multiplier == 1.0
