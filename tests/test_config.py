import pytest

from zozode.config import DEFAULT_PORT, UdpConfig, validate_difficulty


def test_default_port_is_2806():
    assert DEFAULT_PORT == 2806
    assert UdpConfig().port == 2806


def test_address_returns_host_port_tuple():
    config = UdpConfig(host="0.0.0.0", port=12000)

    assert config.address() == ("0.0.0.0", 12000)


def test_validate_rejects_invalid_port():
    config = UdpConfig(port=0)

    with pytest.raises(ValueError, match="port must be between"):
        config.validate()


def test_validate_rejects_invalid_buffer_size():
    config = UdpConfig(buffer_size=0)

    with pytest.raises(ValueError, match="buffer_size must be positive"):
        config.validate()


def test_validate_difficulty_accepts_known_values():
    assert validate_difficulty(0) == 0
    assert validate_difficulty(1) == 1
    assert validate_difficulty(2) == 2


def test_validate_difficulty_rejects_unknown_values():
    with pytest.raises(ValueError, match="difficulty must be 0, 1, or 2"):
        validate_difficulty(3)
