import pytest

from zozode.config import UdpConfig


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
