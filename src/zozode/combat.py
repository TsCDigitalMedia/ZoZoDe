from __future__ import annotations

import math

from zozode.constants import BLINK_SECONDS, BULLET_RADIUS, DOT_RADIUS, HEALTH, RESPAWN_SECONDS
from zozode.player import Bullet, Player
from zozode.player_state import spawn_player


def handle_hits(players: dict[str, Player], now: float) -> None:
    for attacker in players.values():
        if not attacker.alive:
            continue
        active_bullets = []
        for bullet in attacker.bullets:
            if bullet_hits_player(bullet, players, now):
                continue
            active_bullets.append(bullet)
        attacker.bullets = active_bullets


def bullet_hits_player(bullet: Bullet, players: dict[str, Player], now: float) -> bool:
    for target in players.values():
        if target.name == bullet.owner or not target.alive or target.invulnerable_until > now:
            continue
        distance = math.hypot(target.x - bullet.x, target.y - bullet.y)
        if distance <= DOT_RADIUS + BULLET_RADIUS:
            damage_player(target, now)
            return True
    return False


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
        player.indicator_x = fresh.indicator_x
        player.indicator_y = fresh.indicator_y
        player.health = HEALTH
        player.invulnerable_until = 0
        player.respawn_at = 0
        player.alive = True
        player.bullets = []
