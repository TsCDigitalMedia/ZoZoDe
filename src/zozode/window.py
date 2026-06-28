from __future__ import annotations

import socket
import time
import uuid
from typing import Any

import pygame

from zozode.combat import handle_hits, reset_finished_blinks, respawn_dead_players
from zozode.config import DEFAULT_PORT
from zozode.constants import CLIENT_HOST, FPS, HEIGHT, MAX_LENGTH, SERVER_HOST, WIDTH
from zozode.movement import update_local_player, update_remote_player
from zozode.network import make_socket, receive_all, send
from zozode.player import Player
from zozode.player_state import copy_player_state, player_from_payload, player_payload, spawn_player
from zozode.render import draw


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

        reset_finished_blinks(players, now)
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
