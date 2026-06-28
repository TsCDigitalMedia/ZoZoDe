from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import anyio

from zozode.config import UdpConfig

MessageHandler = Callable[[bytes, tuple[str, int]], bytes | None]
JsonMessage = dict[str, Any]


async def send_message_async(message: str, config: UdpConfig) -> None:
    config.validate()
    payload = message.encode(config.encoding)
    sock = await anyio.create_udp_socket(local_host="0.0.0.0")
    try:
        await sock.sendto(payload, config.host, config.port)
    finally:
        await sock.aclose()


def send_message(message: str, config: UdpConfig) -> None:
    anyio.run(send_message_async, message, config)


async def serve_async(config: UdpConfig, handler: MessageHandler | None = None) -> None:
    config.validate()
    sock = await anyio.create_udp_socket(local_host=config.host, local_port=config.port)
    try:
        print(f"UDP server listening on {config.host}:{config.port}")
        while True:
            data, peer = await sock.receive()
            text = data.decode(config.encoding, errors="replace")
            print(f"{peer[0]}:{peer[1]} > {text}")
            if handler is None:
                continue
            response = handler(data, peer)
            if response:
                await sock.sendto(response, peer[0], peer[1])
    finally:
        await sock.aclose()


def serve(config: UdpConfig, handler: MessageHandler | None = None) -> None:
    anyio.run(serve_async, config, handler)


def encode_json(message: JsonMessage, encoding: str = "utf-8") -> bytes:
    return json.dumps(message, separators=(",", ":")).encode(encoding)


def decode_json(data: bytes, encoding: str = "utf-8") -> JsonMessage:
    message = json.loads(data.decode(encoding))
    if not isinstance(message, dict):
        msg = "UDP JSON message must be an object"
        raise ValueError(msg)
    return message
