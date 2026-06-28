from __future__ import annotations

import argparse

from zozode.config import DEFAULT_PORT
from zozode.window import run_client, run_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="zozode", description="Run the ZoZoDe LAN dot game")
    parser.add_argument("--join", metavar="IP", help="join a ZoZoDe server as a client")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="UDP port")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.join:
        run_client(args.join, args.port)
    else:
        run_server(args.port)
    return 0
