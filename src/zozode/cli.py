from __future__ import annotations

import argparse

from zozode.client import main as client_main
from zozode.config import DEFAULT_PORT
from zozode.server import main as server_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="zozode", description="ZoZoDe UDP tools")
    subparsers = parser.add_subparsers(dest="command")

    server = subparsers.add_parser("server", help="run the UDP server")
    add_udp_options(server, host_help="UDP host/address to bind", port_help="UDP port to bind")

    client = subparsers.add_parser("client", help="send one UDP datagram")
    add_udp_options(client, host_help="UDP server host/address", port_help="UDP server port")
    client.add_argument(
        "message",
        nargs="?",
        default="hello from ZoZoDe",
        help="message text to send",
    )

    return parser


def add_udp_options(parser: argparse.ArgumentParser, *, host_help: str, port_help: str) -> None:
    parser.add_argument("--host", default="127.0.0.1", help=host_help)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=port_help)
    parser.add_argument("--buffer-size", type=int, default=65_507, help="receive buffer size")
    parser.add_argument("--encoding", default="utf-8", help="text encoding")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "server":
        return server_main([
            "--host",
            args.host,
            "--port",
            str(args.port),
            "--buffer-size",
            str(args.buffer_size),
            "--encoding",
            args.encoding,
        ])

    if args.command == "client":
        return client_main([
            args.message,
            "--host",
            args.host,
            "--port",
            str(args.port),
            "--buffer-size",
            str(args.buffer_size),
            "--encoding",
            args.encoding,
        ])

    return client_main(argv)
