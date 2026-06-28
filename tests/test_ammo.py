from zozode.ammo import AmmoState, consume_ammo, refresh_reload, reload_progress, start_reload
from zozode.assets import WeaponConfig

TEST_WEAPON = WeaponConfig(
    name="Test",
    rps=5,
    ammo=2,
    reload_time=1.5,
    spread=0,
    is_holdable=False,
)


def test_consume_ammo_decrements_remaining_ammo():
    ammo = AmmoState(TEST_WEAPON)

    assert consume_ammo(ammo, 10.0)

    assert ammo.remaining == 1
    assert ammo.reload_started_at == 0.0


def test_consume_last_ammo_starts_reload():
    ammo = AmmoState(TEST_WEAPON, remaining=1)

    assert consume_ammo(ammo, 10.0)

    assert ammo.remaining == 0
    assert ammo.reload_started_at == 10.0


def test_empty_ammo_blocks_shooting_until_reload_finishes():
    ammo = AmmoState(TEST_WEAPON, remaining=0, reload_started_at=10.0)

    assert not consume_ammo(ammo, 10.5)
    assert reload_progress(ammo, 10.75) == 0.5

    refresh_reload(ammo, 11.5)

    assert ammo.remaining == TEST_WEAPON.ammo
    assert ammo.reload_started_at == 0.0


def test_manual_reload_uses_half_reload_time_and_blocks_shooting():
    ammo = AmmoState(TEST_WEAPON, remaining=1)

    assert start_reload(ammo, 10.0, TEST_WEAPON.reload_time / 2)

    assert not consume_ammo(ammo, 10.25)
    assert reload_progress(ammo, 10.375) == 0.5

    refresh_reload(ammo, 10.75)

    assert ammo.remaining == TEST_WEAPON.ammo
    assert ammo.reload_started_at == 0.0
    assert ammo.reload_duration is None


def test_manual_reload_does_nothing_when_ammo_is_full():
    ammo = AmmoState(TEST_WEAPON)

    assert not start_reload(ammo, 10.0, TEST_WEAPON.reload_time / 2)

    assert ammo.remaining == TEST_WEAPON.ammo
    assert ammo.reload_started_at == 0.0
