from __future__ import annotations

import socket
from typing import Any

from zozode.udp import decode_json, encode_json


def make_socket(host: str, port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    sock.bind((host, port))
    return sock


def send(sock: socket.socket, address: tuple[str, int], message: dict[str, Any]) -> bool:
    try:
        sock.sendto(encode_json(message), address)
    except OSError as error:
        print(f"UDP send failed to {address[0]}:{address[1]}: {error}")
        return False
    return True


def receive_all(sock: socket.socket) -> list[tuple[dict[str, Any], tuple[str, int]]]:
    messages = []
    while True:
        try:
            data, address = sock.recvfrom(65_507)
        except BlockingIOError:
            break
        try:
            messages.append((decode_json(data), address))
        except (UnicodeDecodeError, ValueError):
            continue
    return messages
