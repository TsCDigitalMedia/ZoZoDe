import platform
import shutil
import subprocess

import pytest

from zozode.firewall import allow_udp_port


def test_allow_udp_port_rejects_invalid_port():
    with pytest.raises(ValueError, match="port must be between"):
        allow_udp_port(0)


def test_linux_firewall_skips_when_ufw_is_missing(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(shutil, "which", lambda name: None)

    result = allow_udp_port(2806)

    assert result.platform_name == "linux"
    assert result.command is None
    assert result.applied is False
    assert "ufw was not found" in result.message


def test_linux_firewall_runs_ufw_for_udp_port(monkeypatch):
    calls = []

    def fake_run(command, check, capture_output, text):
        calls.append((command, check, capture_output, text))
        return subprocess.CompletedProcess(command, 0, stdout="Rule added", stderr="")

    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/sbin/ufw")
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = allow_udp_port(2806)

    assert result.command == ("ufw", "allow", "2806/udp")
    assert result.applied is True
    assert result.message == "Rule added"
    assert calls == [(("ufw", "allow", "2806/udp"), False, True, True)]


def test_windows_firewall_runs_netsh_for_udp_port(monkeypatch):
    def fake_run(command, check, capture_output, text):
        return subprocess.CompletedProcess(command, 0, stdout="Ok", stderr="")

    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setattr(shutil, "which", lambda name: "netsh.exe")
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = allow_udp_port(2806)

    assert result.applied is True
    assert result.command == (
        "netsh",
        "advfirewall",
        "firewall",
        "add",
        "rule",
        "name=ZoZoDe UDP 2806",
        "dir=in",
        "action=allow",
        "protocol=UDP",
        "localport=2806",
    )


def test_macos_firewall_reports_port_rules_are_not_supported(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")

    result = allow_udp_port(2806)

    assert result.platform_name == "darwin"
    assert result.applied is False
    assert result.command is None
    assert "does not support per-port allow rules" in result.message
