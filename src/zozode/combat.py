from __future__ import annotations

from zozode.constants import BLINK_SECONDS, DOT_RADIUS, HEALTH, RESPAWN_SECONDS
from zozode.geometry import point_segment_distance
from zozode.player import Player
from zozode.player_state import spawn_player


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


def reset_finished_blinks(players: dict[str, Player], now: float) -> None:
    for player in players.values():
        if player.alive and 0 < player.invulnerable_until <= now:
            player.invulnerable_until = 0


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
        player.invulnerable_until = 0
        player.respawn_at = 0
        player.alive = True
