from __future__ import annotations

import argparse
import sys

from zozode.config import DEFAULT_PORT, UdpConfig
from zozode.udp import send_message


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="zozode", description="Run the ZoZoDe UDP client")
    parser.add_argument(
        "message",
        nargs="?",
        default="hello from ZoZoDe",
        help="message text to send",
    )
    parser.add_argument("--host", default="127.0.0.1", help="UDP server host/address")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="UDP server port")
    parser.add_argument("--buffer-size", type=int, default=65_507, help="receive buffer size")
    parser.add_argument("--encoding", default="utf-8", help="text encoding")
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
    send_message(args.message, config_from_args(args))
    print(f"sent: {args.message}", file=sys.stderr)
    return 0
