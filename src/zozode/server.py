from __future__ import annotations

import argparse

from zozode.config import DEFAULT_PORT, UdpConfig
from zozode.firewall import allow_udp_port, print_firewall_result
from zozode.udp import serve


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="zozode-server", description="Run the ZoZoDe UDP server")
    parser.add_argument("--host", default="127.0.0.1", help="UDP host/address to bind")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="UDP port to bind")
    parser.add_argument("--buffer-size", type=int, default=65_507, help="receive buffer size")
    parser.add_argument("--encoding", default="utf-8", help="text encoding")
    parser.add_argument(
        "--no-firewall",
        action="store_true",
        help="skip automatic firewall allow for the UDP port",
    )
    return parser


def config_from_args(args: argparse.Namespace) -> UdpConfig:
    return UdpConfig(
        host=args.host,
        port=args.port,
        buffer_size=args.buffer_size,
        encoding=args.encoding,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = config_from_args(args)
    if not args.no_firewall:
        print_firewall_result(allow_udp_port(config.port))
    serve(config)
    return 0
