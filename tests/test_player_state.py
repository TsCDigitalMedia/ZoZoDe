from zozode.assets import WeaponConfig
from zozode.magazine import MagazineState
from zozode.player import Player
from zozode.player_state import changed_values, recorded_stats, player_from_payload, player_payload, sync_recorded_stats


TEST_WEAPON = WeaponConfig(
    name="Test",
    rps=5,
    magazine=10,
    reload_time=1.5,
    spread=0,
    damage=1,
    is_holdable=False,
)


def test_recorded_stats_include_magazine_health_and_score():
    player = Player(
        name="player",
        x=0,
        y=0,
        color=(255, 255, 255),
        indicator_color=(255, 255, 255),
        indicator_x=0,
        indicator_y=0,
        health=2,
    )
    magazine = MagazineState(TEST_WEAPON, remaining=4)

    stats = recorded_stats(player, magazine, 12)

    assert stats == {
        "magazine": 4,
        "health": 2,
        "score": 12,
    }


def test_recorded_stats_reset_to_defaults_for_dead_player():
    player = Player(
        name="player",
        x=0,
        y=0,
        color=(255, 255, 255),
        indicator_color=(255, 255, 255),
        indicator_x=0,
        indicator_y=0,
        health=1,
        alive=False,
    )
    magazine = MagazineState(TEST_WEAPON, remaining=4)

    stats = recorded_stats(player, magazine, 12)

    assert stats == {
        "magazine": TEST_WEAPON.magazine,
        "health": 3,
        "score": 0,
    }


def test_player_payload_round_trips_shared_statistics():
    player = Player(
        name="player",
        x=0,
        y=0,
        color=(255, 255, 255),
        indicator_color=(255, 255, 255),
        indicator_x=0,
        indicator_y=0,
        health=2,
    )
    magazine = MagazineState(TEST_WEAPON, remaining=4)
    recorded_stats(player, magazine, 12)

    restored = player_from_payload(player_payload(player))

    assert restored.statistics.magazine == 4
    assert restored.statistics.health == 2
    assert restored.statistics.score == 12


def test_sync_recorded_stats_resets_dead_player_actual_magazine():
    player = Player(
        name="player",
        x=0,
        y=0,
        color=(255, 255, 255),
        indicator_color=(255, 255, 255),
        indicator_x=0,
        indicator_y=0,
        health=1,
        alive=False,
    )
    magazine = MagazineState(TEST_WEAPON, remaining=4, reload_started_at=10.0, reload_duration=1.0)

    sync_recorded_stats(player, magazine)

    assert magazine.remaining == TEST_WEAPON.magazine
    assert magazine.reload_started_at == 0.0
    assert magazine.reload_duration is None
    assert player.statistics.magazine == TEST_WEAPON.magazine
    assert player.statistics.health == 3
    assert player.statistics.score == 0


def test_changed_values_only_returns_updated_fields():
    previous = {}

    assert changed_values({"x": 1.0, "y": 2.0}, previous) == {"x": 1.0, "y": 2.0}
    assert changed_values({"x": 1.0, "y": 3.0}, previous) == {"y": 3.0}
    assert changed_values({"x": 1.0, "y": 3.0}, previous) == {}
