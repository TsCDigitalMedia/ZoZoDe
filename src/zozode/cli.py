from __future__ import annotations

import argparse

from zozode.config import DEFAULT_PORT, validate_difficulty
from zozode.window import run_client, run_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="zozode", description="Run the ZoZoDe LAN dot game")
    parser.add_argument("--join", metavar="IP", help="join a ZoZoDe server as a client")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="UDP port")
    parser.add_argument(
        "--difficulty",
        type=int,
        default=1,
        choices=(0, 1, 2),
        help="difficulty: Easy=0, Normal=1, Hard=2",
    )
    parser.add_argument(
        "--friendly-fire",
        action="store_true",
        help="allow player bullets to damage other players",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.join:
        run_client(args.join, args.port)
    else:
        run_server(args.port, validate_difficulty(args.difficulty), args.friendly_fire)
    return 0
