from __future__ import annotations

import socket
import time
import uuid
from typing import Any

import pygame

from zozode.bullets import DEFAULT_WEAPON, maybe_spawn_bullet, step_bullets
from zozode.combat import handle_hits, reset_finished_blinks, respawn_dead_players
from zozode.config import DEFAULT_PORT
from zozode.constants import CLIENT_HOST, DIFFICULTY_NAMES, FPS, HEIGHT, SERVER_HOST, WIDTH
from zozode.enemies import handle_enemy_hits, maybe_spawn_enemy, step_enemies
from zozode.movement import lerp_remote_player, update_local_player, update_remote_player
from zozode.network import make_socket, receive_all, send
from zozode.player import Enemy, Player
from zozode.player_state import (
    copy_player_state,
    enemy_from_payload,
    enemy_payload,
    player_from_payload,
    player_payload,
    spawn_player,
)
from zozode.render import draw


def run_server(port: int = DEFAULT_PORT, difficulty: int = 1, friendly_fire: bool = False) -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ZoZoDe server")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    sock = make_socket(SERVER_HOST, port)
    server_id = "server"
    players: dict[str, Player] = {server_id: spawn_player(server_id)}
    peers: dict[str, tuple[str, int]] = {}
    next_shot_at: dict[str, float] = {server_id: 0.0}
    enemies: list[Enemy] = []
    next_enemy_spawn_at = time.monotonic()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        now = time.monotonic()
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        mouse_pressed = pygame.mouse.get_pressed()[0]
        mouse_clicked = any(
            event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 for event in events
        )
        if mouse_pressed if DEFAULT_WEAPON.is_holdable else mouse_clicked:
            bullet, next_shot_at[server_id] = maybe_spawn_bullet(
                players[server_id],
                pygame.mouse.get_pos(),
                now,
                next_shot_at[server_id],
            )
            if bullet is not None:
                players[server_id].bullets.append(bullet)

        reset_finished_blinks(players, now)
        respawn_dead_players(players, now)
        keys = pygame.key.get_pressed()
        update_local_player(players[server_id], keys, pygame.mouse.get_pos(), dt)

        for message, address in receive_all(sock):
            kind = message.get("type")
            if kind == "join":
                accept_player(sock, address, message, players, peers)
                next_shot_at[str(message.get("id") or "")] = 0.0
            elif kind == "move":
                update_remote_player(message, players)
            elif kind == "shoot":
                spawn_remote_bullet(message, players, next_shot_at, now)

        step_bullets(players, dt)
        handle_hits(players, now, friendly_fire)
        handle_enemy_hits(enemies, players)
        next_enemy_spawn_at = maybe_spawn_enemy(
            enemies,
            players,
            now,
            next_enemy_spawn_at,
            difficulty,
        )
        step_enemies(enemies, players, dt, now, difficulty)
        state = {
            "type": "state",
            "players": [player_payload(player) for player in players.values()],
            "enemies": [enemy_payload(enemy) for enemy in enemies],
            "difficulty": difficulty,
        }
        disconnected = []
        for player_id, address in peers.items():
            if not send(sock, address, state):
                disconnected.append(player_id)
        for player_id in disconnected:
            peers.pop(player_id, None)
            players.pop(player_id, None)
            next_shot_at.pop(player_id, None)

        difficulty_name = DIFFICULTY_NAMES.get(difficulty, str(difficulty))
        ff = "on" if friendly_fire else "off"
        draw(
            screen,
            font,
            players.values(),
            f"Server UDP :{port}  {difficulty_name}  FF {ff}  click shoots",
            enemies,
        )

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
    players[player_id] = spawn_player(player_id)
    if not send(
        sock,
        address,
        {
            "type": "welcome",
            "id": player_id,
            "players": list(map(player_payload, players.values())),
        },
    ):
        peers.pop(player_id, None)
        players.pop(player_id, None)


def spawn_remote_bullet(
    message: dict[str, Any],
    players: dict[str, Player],
    next_shot_at: dict[str, float],
    now: float,
) -> None:
    player_id = str(message.get("id"))
    if player_id not in players or not players[player_id].alive:
        return
    mouse_pos = (
        int(message.get("mouse_x", players[player_id].indicator_x)),
        int(message.get("mouse_y", players[player_id].indicator_y)),
    )
    bullet, next_shot_at[player_id] = maybe_spawn_bullet(
        players[player_id],
        mouse_pos,
        now,
        next_shot_at.get(player_id, 0.0),
    )
    if bullet is not None:
        players[player_id].bullets.append(bullet)


def run_client(host: str, port: int = DEFAULT_PORT) -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"ZoZoDe client -> {host}:{port}")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    sock = make_socket(CLIENT_HOST, 0)
    server = (host, port)
    player_id = uuid.uuid4().hex
    local_player = spawn_player(player_id)
    local_player.x = WIDTH / 2
    local_player.y = HEIGHT / 2
    players: dict[str, Player] = {player_id: local_player}
    next_shot_at = 0.0
    enemies: list[Enemy] = []
    send(sock, server, {"type": "join", "id": player_id})

    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        mouse_pos = pygame.mouse.get_pos()
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        mouse_pressed = pygame.mouse.get_pressed()[0]
        mouse_clicked = any(
            event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 for event in events
        )
        if mouse_pressed if DEFAULT_WEAPON.is_holdable else mouse_clicked:
            bullet, next_shot_at = maybe_spawn_bullet(
                local_player,
                mouse_pos,
                time.monotonic(),
                next_shot_at,
            )
            if bullet is not None:
                local_player.bullets.append(bullet)
                send(
                    sock,
                    server,
                    {
                        "type": "shoot",
                        "id": player_id,
                        "mouse_x": mouse_pos[0],
                        "mouse_y": mouse_pos[1],
                    },
                )

        keys = pygame.key.get_pressed()
        update_local_player(local_player, keys, mouse_pos, dt)
        step_bullets(players, dt)
        send(
            sock,
            server,
            {
                "type": "move",
                "id": player_id,
                "x": local_player.x,
                "y": local_player.y,
                "mouse_x": mouse_pos[0],
                "mouse_y": mouse_pos[1],
            },
        )

        for message, _address in receive_all(sock):
            if message.get("type") in {"welcome", "state"}:
                sync_players(message, players, player_id, local_player)
                sync_enemies(message, enemies)

        draw(screen, font, players.values(), f"Client {host}:{port}  click shoots", enemies)

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
        if player.name == player_id:
            copy_player_state(local_player, player)
            players[player_id] = local_player
        elif player.name in players:
            lerp_remote_player(players[player.name], player)
        else:
            players[player.name] = player


def sync_enemies(message: dict[str, Any], enemies: list[Enemy]) -> None:
    enemies[:] = [enemy_from_payload(payload) for payload in message.get("enemies", [])]
