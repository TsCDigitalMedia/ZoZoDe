from __future__ import annotations

import math
import random
import socket
import time
import uuid
from collections.abc import Iterable
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
MAX_LENGTH = 120
HEALTH = 3
BLINK_SECONDS = 2
RESPAWN_SECONDS = 2
FPS = 60
SERVER_HOST = '0.0.0.0'
CLIENT_HOST = '0.0.0.0'


def random_color() -> tuple[int, int, int]:
    return random.randint(80, 255), random.randint(80, 255), random.randint(80, 255)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def make_socket(host: str, port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    sock.bind((host, port))
    return sock


def send(sock: socket.socket, address: tuple[str, int], message: dict[str, Any]) -> bool:
    try:
        sock.sendto(encode_json(message), address)
    except OSError as error:
        print(f'UDP send failed to {address[0]}:{address[1]}: {error}')
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


def capped_sword_endpoint(
    player: Player,
    mouse_x: float,
    mouse_y: float,
    max_length: float,
) -> tuple[float, float]:
    dx = mouse_x - player.x
    dy = mouse_y - player.y
    length = math.hypot(dx, dy)
    if length == 0:
        return player.x, player.y
    scale = min(max_length, length) / length
    return player.x + dx * scale, player.y + dy * scale


def point_segment_distance(
    point_x: float,
    point_y: float,
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
) -> float:
    segment_x = end_x - start_x
    segment_y = end_y - start_y
    length_squared = segment_x * segment_x + segment_y * segment_y
    if length_squared == 0:
        return math.hypot(point_x - start_x, point_y - start_y)
    t = ((point_x - start_x) * segment_x + (point_y - start_y) * segment_y) / length_squared
    t = clamp(t, 0, 1)
    closest_x = start_x + t * segment_x
    closest_y = start_y + t * segment_y
    return math.hypot(point_x - closest_x, point_y - closest_y)


def spawn_player(name: str) -> Player:
    x = random.randint(DOT_RADIUS, WIDTH - DOT_RADIUS)
    y = random.randint(DOT_RADIUS, HEIGHT - DOT_RADIUS)
    return Player(
        name=name,
        x=x,
        y=y,
        color=random_color(),
        sword_color=random_color(),
        sword_x=x,
        sword_y=y,
        health=HEALTH,
    )


def player_payload(player: Player) -> dict[str, Any]:
    payload = asdict(player)
    payload['color'] = list(player.color)
    payload['sword_color'] = list(player.sword_color)
    return payload


def player_from_payload(payload: dict[str, Any]) -> Player:
    color = payload.get('color', [255, 255, 255])
    sword_color = payload.get('sword_color', color)
    return Player(
        name=str(payload['name']),
        x=float(payload['x']),
        y=float(payload['y']),
        color=(int(color[0]), int(color[1]), int(color[2])),
        sword_color=(int(sword_color[0]), int(sword_color[1]), int(sword_color[2])),
        sword_x=float(payload.get('sword_x', payload['x'])),
        sword_y=float(payload.get('sword_y', payload['y'])),
        health=int(payload.get('health', HEALTH)),
        invulnerable_until=float(payload.get('invulnerable_until', 0)),
        respawn_at=float(payload.get('respawn_at', 0)),
        alive=bool(payload.get('alive', True)),
    )


def copy_player_state(target: Player, source: Player) -> None:
    target.x = source.x
    target.y = source.y
    target.color = source.color
    target.sword_color = source.sword_color
    target.sword_x = source.sword_x
    target.sword_y = source.sword_y
    target.health = source.health
    target.invulnerable_until = source.invulnerable_until
    target.respawn_at = source.respawn_at
    target.alive = source.alive


def run_server(port: int = DEFAULT_PORT, max_length: float = MAX_LENGTH) -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('ZoZoDe server')
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    sock = make_socket(SERVER_HOST, port)
    server_id = 'server'
    players: dict[str, Player] = {server_id: spawn_player(server_id)}
    peers: dict[str, tuple[str, int]] = {}

    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        now = time.monotonic()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        respawn_dead_players(players, now)
        keys = pygame.key.get_pressed()
        update_local_player(players[server_id], keys, pygame.mouse.get_pos(), dt, max_length)

        for message, address in receive_all(sock):
            kind = message.get('type')
            if kind == 'join':
                accept_player(sock, address, message, players, peers, max_length)
            elif kind == 'move':
                update_remote_player(message, players, max_length)

        handle_hits(players, now)
        state = {
            'type': 'state',
            'max_length': max_length,
            'players': [player_payload(player) for player in players.values()],
        }
        disconnected = []
        for player_id, address in peers.items():
            if not send(sock, address, state):
                disconnected.append(player_id)
        for player_id in disconnected:
            peers.pop(player_id, None)
            players.pop(player_id, None)

        draw(screen, font, players.values(), f'Server UDP :{port}  mouse aims sword')

    sock.close()
    pygame.quit()


def accept_player(
    sock: socket.socket,
    address: tuple[str, int],
    message: dict[str, Any],
    players: dict[str, Player],
    peers: dict[str, tuple[str, int]],
    max_length: float,
) -> None:
    player_id = str(message.get('id') or uuid.uuid4().hex)
    peers[player_id] = address
    players[player_id] = spawn_player(player_id)
    if not send(
        sock,
        address,
        {
            'type': 'welcome',
            'id': player_id,
            'max_length': max_length,
            'players': list(map(player_payload, players.values())),
        },
    ):
        peers.pop(player_id, None)
        players.pop(player_id, None)


def update_remote_player(
    message: dict[str, Any],
    players: dict[str, Player],
    max_length: float,
) -> None:
    player_id = str(message.get('id'))
    if player_id not in players:
        return
    player = players[player_id]
    if not player.alive:
        return
    player.x = clamp(float(message.get('x', player.x)), DOT_RADIUS, WIDTH - DOT_RADIUS)
    player.y = clamp(float(message.get('y', player.y)), DOT_RADIUS, HEIGHT - DOT_RADIUS)
    mouse_x = float(message.get('mouse_x', player.sword_x))
    mouse_y = float(message.get('mouse_y', player.sword_y))
    player.sword_x, player.sword_y = capped_sword_endpoint(player, mouse_x, mouse_y, max_length)


def update_local_player(
    player: Player,
    keys: pygame.key.ScancodeWrapper,
    mouse_pos: tuple[int, int],
    dt: float,
    max_length: float,
) -> None:
    if not player.alive:
        return
    dx = float(keys[pygame.K_d]) - float(keys[pygame.K_a])
    dy = float(keys[pygame.K_s]) - float(keys[pygame.K_w])
    player.x = clamp(player.x + dx * SPEED * dt, DOT_RADIUS, WIDTH - DOT_RADIUS)
    player.y = clamp(player.y + dy * SPEED * dt, DOT_RADIUS, HEIGHT - DOT_RADIUS)
    player.sword_x, player.sword_y = capped_sword_endpoint(
        player,
        mouse_pos[0],
        mouse_pos[1],
        max_length,
    )


def handle_hits(players: dict[str, Player], now: float) -> None:
    live_players = [player for player in players.values() if player.alive]
    for attacker in live_players:
        for target in live_players:
            if attacker.name == target.name or target.invulnerable_until > now:
                continue
            distance = point_segment_distance(
                target.x,
                target.y,
                attacker.x,
                attacker.y,
                attacker.sword_x,
                attacker.sword_y,
            )
            if distance <= DOT_RADIUS:
                damage_player(target, now)


def damage_player(player: Player, now: float) -> None:
    player.health = max(0, player.health - 1)
    if player.health == 0:
        player.alive = False
        player.respawn_at = now + RESPAWN_SECONDS
        player.invulnerable_until = 0
    else:
        player.invulnerable_until = now + BLINK_SECONDS


def respawn_dead_players(players: dict[str, Player], now: float) -> None:
    for player in players.values():
        if player.alive or player.respawn_at > now:
            continue
        fresh = spawn_player(player.name)
        player.x = fresh.x
        player.y = fresh.y
        player.sword_x = fresh.sword_x
        player.sword_y = fresh.sword_y
        player.health = HEALTH
        player.respawn_at = 0
        player.alive = True


def run_client(host: str, port: int = DEFAULT_PORT) -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f'ZoZoDe client -> {host}:{port}')
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    sock = make_socket(CLIENT_HOST, 0)
    server = (host, port)
    player_id = uuid.uuid4().hex
    local_player = spawn_player(player_id)
    local_player.x = WIDTH / 2
    local_player.y = HEIGHT / 2
    players: dict[str, Player] = {player_id: local_player}
    max_length = float(MAX_LENGTH)
    send(sock, server, {'type': 'join', 'id': player_id})

    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        update_local_player(local_player, keys, mouse_pos, dt, max_length)
        send(
            sock,
            server,
            {
                'type': 'move',
                'id': player_id,
                'x': local_player.x,
                'y': local_player.y,
                'mouse_x': mouse_pos[0],
                'mouse_y': mouse_pos[1],
            },
        )

        for message, _address in receive_all(sock):
            if message.get('type') in {'welcome', 'state'}:
                max_length = float(message.get('max_length', max_length))
                sync_players(message, players, player_id, local_player)

        draw(screen, font, players.values(), f'Client {host}:{port}  mouse aims sword')

    sock.close()
    pygame.quit()


def sync_players(
    message: dict[str, Any],
    players: dict[str, Player],
    player_id: str,
    local_player: Player,
) -> None:
    for payload in message.get('players', []):
        player = player_from_payload(payload)
        players[player.name] = player
    if player_id not in players:
        return
    copy_player_state(local_player, players[player_id])
    players[player_id] = local_player


def draw(
    screen: pygame.Surface,
    font: pygame.font.Font,
    players: Iterable[Player],
    status: str,
) -> None:
    now = time.monotonic()
    screen.fill((20, 20, 24))
    for player in players:
        if not player.alive:
            continue
        blinking = player.invulnerable_until > now and int(now * 10) % 2 == 0
        if blinking:
            continue
        pygame.draw.line(
            screen,
            player.sword_color,
            (round(player.x), round(player.y)),
            (round(player.sword_x), round(player.sword_y)),
            4,
        )
        pygame.draw.circle(screen, player.color, (round(player.x), round(player.y)), DOT_RADIUS)
        health = font.render(str(player.health), True, (240, 240, 240))
        screen.blit(health, (round(player.x) - 5, round(player.y) - 30))
    text = font.render(status, True, (230, 230, 230))
    screen.blit(text, (12, 12))
    pygame.display.flip()
