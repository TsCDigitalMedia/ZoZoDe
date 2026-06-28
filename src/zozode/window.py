from __future__ import annotations

import random
import socket
import uuid
from dataclasses import asdict
from typing import Any

import pygame

from zozode.config import DEFAULT_PORT
from zozode.player import Player
from zozode.udp import decode_json, encode_json

WIDTH = 800
HEIGHT = 600
DOT_RADIUS = 10
SPEED = 220
FPS = 60
SERVER_HOST = "0.0.0.0"
LOCALHOST = "127.0.0.1"


def random_color() -> tuple[int, int, int]:
    return random.randint(80, 255), random.randint(80, 255), random.randint(80, 255)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def make_socket(host: str, port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    sock.bind((host, port))
    return sock


def send(sock: socket.socket, address: tuple[str, int], message: dict[str, Any]) -> None:
    sock.sendto(encode_json(message), address)


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


def player_payload(player: Player) -> dict[str, Any]:
    payload = asdict(player)
    payload["color"] = list(player.color)
    return payload


def player_from_payload(payload: dict[str, Any]) -> Player:
    color = payload.get("color", [255, 255, 255])
    return Player(
        name=str(payload["name"]),
        x=float(payload["x"]),
        y=float(payload["y"]),
        color=(int(color[0]), int(color[1]), int(color[2])),
    )


def run_server(port: int = DEFAULT_PORT) -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ZoZoDe server")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    sock = make_socket(SERVER_HOST, port)
    server_id = "server"
    players: dict[str, Player] = {
        server_id: Player(server_id, WIDTH / 2, HEIGHT / 2, random_color()),
    }
    peers: dict[str, tuple[str, int]] = {}

    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        move_player(players[server_id], keys, dt)

        for message, address in receive_all(sock):
            kind = message.get("type")
            if kind == "join":
                accept_player(sock, address, message, players, peers)
            elif kind == "move":
                update_remote_player(message, players)

        state = {
            "type": "state",
            "players": [player_payload(player) for player in players.values()],
        }
        for address in peers.values():
            send(sock, address, state)

        draw(screen, font, players.values(), f"Server UDP :{port}  WASD moves server dot")

    sock.close()
    pygame.quit()


def accept_player(
    sock: socket.socket,
    address: tuple[str, int],
    message: dict[str, Any],
    players: dict[str, Player],
    peers: dict[str, tuple[str, int]],
) -> None:
    player_id = str(message.get("id") or uuid.uuid4().hex)
    peers[player_id] = address
    players[player_id] = Player(
        player_id,
        random.randint(DOT_RADIUS, WIDTH - DOT_RADIUS),
        random.randint(DOT_RADIUS, HEIGHT - DOT_RADIUS),
        random_color(),
    )
    send(
        sock,
        address,
        {
            "type": "welcome",
            "id": player_id,
            "players": list(map(player_payload, players.values())),
        },
    )


def update_remote_player(message: dict[str, Any], players: dict[str, Player]) -> None:
    player_id = str(message.get("id"))
    if player_id not in players:
        return
    player = players[player_id]
    player.x = clamp(float(message.get("x", player.x)), DOT_RADIUS, WIDTH - DOT_RADIUS)
    player.y = clamp(float(message.get("y", player.y)), DOT_RADIUS, HEIGHT - DOT_RADIUS)


def run_client(host: str, port: int = DEFAULT_PORT) -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"ZoZoDe client -> {host}:{port}")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    sock = make_socket(LOCALHOST, 0)
    server = (host, port)
    player_id = uuid.uuid4().hex
    local_player = Player(player_id, WIDTH / 2, HEIGHT / 2, random_color())
    players: dict[str, Player] = {player_id: local_player}
    send(sock, server, {"type": "join", "id": player_id})

    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        move_player(local_player, keys, dt)
        send(
            sock,
            server,
            {"type": "move", "id": player_id, "x": local_player.x, "y": local_player.y},
        )

        for message, _address in receive_all(sock):
            if message.get("type") in {"welcome", "state"}:
                sync_players(message, players, player_id, local_player)

        draw(screen, font, players.values(), f"Client {host}:{port}  WASD moves your dot")

    sock.close()
    pygame.quit()


def sync_players(
    message: dict[str, Any],
    players: dict[str, Player],
    player_id: str,
    local_player: Player,
) -> None:
    for payload in message.get("players", []):
        player = player_from_payload(payload)
        players[player.name] = player
    if player_id not in players:
        return
    local_player.color = players[player_id].color
    if message.get("type") == "welcome":
        local_player.x = players[player_id].x
        local_player.y = players[player_id].y
    players[player_id] = local_player


def move_player(player: Player, keys: pygame.key.ScancodeWrapper, dt: float) -> None:
    dx = float(keys[pygame.K_d]) - float(keys[pygame.K_a])
    dy = float(keys[pygame.K_s]) - float(keys[pygame.K_w])
    player.x = clamp(player.x + dx * SPEED * dt, DOT_RADIUS, WIDTH - DOT_RADIUS)
    player.y = clamp(player.y + dy * SPEED * dt, DOT_RADIUS, HEIGHT - DOT_RADIUS)


def draw(
    screen: pygame.Surface,
    font: pygame.font.Font,
    players: list[Player] | Any,
    status: str,
) -> None:
    screen.fill((20, 20, 24))
    for player in players:
        pygame.draw.circle(screen, player.color, (round(player.x), round(player.y)), DOT_RADIUS)
    text = font.render(status, True, (230, 230, 230))
    screen.blit(text, (12, 12))
    pygame.display.flip()
