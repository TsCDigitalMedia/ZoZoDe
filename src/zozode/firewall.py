from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FirewallResult:
    platform_name: str
    command: tuple[str, ...] | None
    applied: bool
    message: str


class FirewallError(RuntimeError):
    pass


def allow_udp_port(port: int, *, rule_name: str = "ZoZoDe UDP") -> FirewallResult:
    if not 1 <= port <= 65_535:
        msg = f"port must be between 1 and 65535, got {port}"
        raise ValueError(msg)

    system = platform.system().lower()
    if system == "linux":
        return _allow_linux(port)
    if system == "windows":
        return _allow_windows(port, rule_name)
    if system == "darwin":
        return FirewallResult(
            platform_name="darwin",
            command=None,
            applied=False,
            message=(
                "macOS application firewall does not support per-port allow rules from this app"
            ),
        )

    return FirewallResult(
        platform_name=system or "unknown",
        command=None,
        applied=False,
        message="automatic firewall allow is not supported on this platform",
    )


def _allow_linux(port: int) -> FirewallResult:
    if shutil.which("ufw") is None:
        return FirewallResult(
            platform_name="linux",
            command=None,
            applied=False,
            message="ufw was not found; skipped automatic firewall allow",
        )

    command = ("ufw", "allow", f"{port}/udp")
    return _run_command("linux", command)


def _allow_windows(port: int, rule_name: str) -> FirewallResult:
    if shutil.which("netsh") is None:
        return FirewallResult(
            platform_name="windows",
            command=None,
            applied=False,
            message="netsh was not found; skipped automatic firewall allow",
        )

    command = (
        "netsh",
        "advfirewall",
        "firewall",
        "add",
        "rule",
        f"name={rule_name} {port}",
        "dir=in",
        "action=allow",
        "protocol=UDP",
        f"localport={port}",
    )
    return _run_command("windows", command)


def _run_command(platform_name: str, command: tuple[str, ...]) -> FirewallResult:
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
    except PermissionError as error:
        return FirewallResult(
            platform_name=platform_name,
            command=command,
            applied=False,
            message=f"permission denied while applying firewall rule: {error}",
        )

    output = (completed.stdout or completed.stderr).strip()
    if completed.returncode == 0:
        return FirewallResult(
            platform_name=platform_name,
            command=command,
            applied=True,
            message=output or "firewall rule applied",
        )

    return FirewallResult(
        platform_name=platform_name,
        command=command,
        applied=False,
        message=output or f"firewall command failed with exit code {completed.returncode}",
    )


def print_firewall_result(result: FirewallResult) -> None:
    status = "applied" if result.applied else "skipped"
    print(f"firewall {status}: {result.message}", file=sys.stderr)
