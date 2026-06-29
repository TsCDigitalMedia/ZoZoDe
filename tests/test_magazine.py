from zozode.assets import WeaponConfig
from zozode.magazine import (
    MagazineState,
    consume_magazine,
    refresh_reload,
    reload_progress,
    start_reload,
)

TEST_WEAPON = WeaponConfig(
    name="Test",
    rps=5,
    magazine=2,
    reload_time=1.5,
    spread=0,
    is_holdable=False,
)


def test_consume_magazine_decrements_remaining_magazine():
    magazine = MagazineState(TEST_WEAPON)

    assert consume_magazine(magazine, 10.0)

    assert magazine.remaining == 1
    assert magazine.reload_started_at == 0.0


def test_consume_last_magazine_starts_reload():
    magazine = MagazineState(TEST_WEAPON, remaining=1)

    assert consume_magazine(magazine, 10.0)

    assert magazine.remaining == 0
    assert magazine.reload_started_at == 10.0


def test_empty_magazine_blocks_shooting_until_reload_finishes():
    magazine = MagazineState(TEST_WEAPON, remaining=0, reload_started_at=10.0)

    assert not consume_magazine(magazine, 10.5)
    assert reload_progress(magazine, 10.75) == 0.5

    refresh_reload(magazine, 11.5)

    assert magazine.remaining == TEST_WEAPON.magazine
    assert magazine.reload_started_at == 0.0


def test_manual_reload_uses_half_reload_time_and_blocks_shooting():
    magazine = MagazineState(TEST_WEAPON, remaining=1)

    assert start_reload(magazine, 10.0, TEST_WEAPON.reload_time / 2)

    assert not consume_magazine(magazine, 10.25)
    assert reload_progress(magazine, 10.375) == 0.5

    refresh_reload(magazine, 10.75)

    assert magazine.remaining == TEST_WEAPON.magazine
    assert magazine.reload_started_at == 0.0
    assert magazine.reload_duration is None


def test_manual_reload_does_nothing_when_magazine_is_full():
    magazine = MagazineState(TEST_WEAPON)

    assert not start_reload(magazine, 10.0, TEST_WEAPON.reload_time / 2)

    assert magazine.remaining == TEST_WEAPON.magazine
    assert magazine.reload_started_at == 0.0
