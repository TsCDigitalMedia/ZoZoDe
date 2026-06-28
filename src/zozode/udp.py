from __future__ import annotations

import socket
from collections.abc import Callable

from zozode.config import UdpConfig

MessageHandler = Callable[[bytes, tuple[str, int]], bytes | None]


def send_message(message: str, config: UdpConfig) -> None:
    config.validate()
    payload = message.encode(config.encoding)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(payload, config.address())


def serve(config: UdpConfig, handler: MessageHandler | None = None) -> None:
    config.validate()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(config.address())
        print(f"UDP server listening on {config.host}:{config.port}")
        while True:
            data, peer = sock.recvfrom(config.buffer_size)
            text = data.decode(config.encoding, errors="replace")
            print(f"{peer[0]}:{peer[1]} > {text}")
            if handler is None:
                continue
            response = handler(data, peer)
            if response:
                sock.sendto(response, peer)
