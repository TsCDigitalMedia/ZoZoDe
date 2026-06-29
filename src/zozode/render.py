from __future__ import annotations

import io
import math
import subprocess
import tempfile
import time
from collections.abc import Iterable
from pathlib import Path

import pygame

from zozode.camera import camera_offset, world_to_screen
from zozode.constants import (
    BULLET_RADIUS,
    DOT_RADIUS,
    ENEMY_RADIUS,
    HEIGHT,
    WIDTH,
)
from zozode.level import DEFAULT_LEVEL, Level, LevelShape
from zozode.magazine import MagazineState, reload_progress
from zozode.player import Enemy, Player
from zozode.powerups import POWERUP_OPTIONS, powerup_button_rects, should_show_powerups

_TEXTURE_CACHE: dict[int, pygame.Surface | None] = {}


def draw(
    screen: pygame.Surface,
    font: pygame.font.Font,
    players: Iterable[Player],
    status: str,
    enemies: Iterable[Enemy] = (),
    magazine: MagazineState | None = None,
    camera_player: Player | None = None,
    score: int = 0,
    level: Level = DEFAULT_LEVEL,
) -> None:
    now = time.monotonic()
    offset = camera_offset(camera_player, level) if camera_player is not None else (0.0, 0.0)
    screen.fill((20, 20, 24))
    arena_rect = pygame.Rect(round(-offset[0]), round(-offset[1]), level.width, level.height)
    pygame.draw.rect(screen, (55, 55, 64), arena_rect, 2)
    if not draw_level_texture(screen, level, offset):
        for shape in level.textures:
            draw_level_shape(screen, shape, offset)
    for enemy in enemies:
        pygame.draw.circle(
            screen,
            (230, 20, 20),
            world_to_screen(enemy.x, enemy.y, offset),
            ENEMY_RADIUS,
        )
    for player in players:
        for bullet in player.bullets:
            pygame.draw.circle(
                screen,
                player.indicator_color,
                world_to_screen(bullet.x, bullet.y, offset),
                BULLET_RADIUS,
            )
        if not player.alive:
            continue
        blinking = player.invulnerable_until > now and int(now * 10) % 2 == 0
        if blinking:
            continue
        player_pos = world_to_screen(player.x, player.y, offset)
        pygame.draw.line(
            screen,
            player.indicator_color,
            player_pos,
            world_to_screen(player.indicator_x, player.indicator_y, offset),
            3,
        )
        pygame.draw.circle(screen, player.color, player_pos, DOT_RADIUS)
        health = font.render(str(player.statistics.health or player.health), True, (240, 240, 240))
        screen.blit(health, (player_pos[0] - 5, player_pos[1] - 30))
    if magazine is not None:
        draw_magazine(screen, magazine, now)
    text = font.render(status, True, (230, 230, 230))
    screen.blit(text, (12, 12))
    score_text = font.render(f"Score {score}", True, (230, 230, 230))
    screen.blit(score_text, (WIDTH - score_text.get_width() - 12, 12))
    if should_show_powerups(score):
        draw_powerups(screen, font, score)
    pygame.display.flip()


def draw_level_texture(
    screen: pygame.Surface,
    level: Level,
    offset: tuple[float, float],
) -> bool:
    texture = level_texture(level)
    if texture is None:
        return False
    screen.blit(texture, (round(-offset[0]), round(-offset[1])))
    return True


def level_texture(level: Level) -> pygame.Surface | None:
    key = id(level)
    if key in _TEXTURE_CACHE:
        return _TEXTURE_CACHE[key]
    if not level.texture_svg:
        _TEXTURE_CACHE[key] = None
        return None
    texture = render_level_svg_with_inkscape(level) or render_level_svg_with_cairosvg(level)
    _TEXTURE_CACHE[key] = texture
    return texture


def render_level_svg_with_inkscape(level: Level) -> pygame.Surface | None:
    inkscape = Path("/snap/bin/inkscape")
    command = str(inkscape) if inkscape.exists() else "inkscape"
    try:
        with tempfile.TemporaryDirectory(dir=".") as directory:
            svg_path = Path(directory) / "level.svg"
            png_path = Path(directory) / "level.png"
            svg_path.write_text(level.texture_svg or "", encoding="utf-8")
            subprocess.run(
                [
                    command,
                    str(svg_path),
                    "--export-type=png",
                    f"--export-filename={png_path}",
                    f"--export-width={round(level.width)}",
                    f"--export-height={round(level.height)}",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return pygame.image.load(str(png_path)).convert_alpha()
    except Exception:
        return None


def render_level_svg_with_cairosvg(level: Level) -> pygame.Surface | None:
    try:
        import cairosvg

        payload = cairosvg.svg2png(
            bytestring=level.texture_svg.encode("utf-8"),
            output_width=round(level.width),
            output_height=round(level.height),
        )
        return pygame.image.load(io.BytesIO(payload), "level.png").convert_alpha()
    except Exception:
        return None


def draw_level_shape(
    screen: pygame.Surface,
    shape: LevelShape,
    offset: tuple[float, float],
) -> None:
    color = shape.color or (74, 70, 70)
    if shape.kind == "rect":
        rect = pygame.Rect(
            round(shape.x - offset[0]),
            round(shape.y - offset[1]),
            round(shape.width),
            round(shape.height),
        )
        pygame.draw.rect(screen, color, rect)
    elif shape.kind == "circle":
        pygame.draw.circle(
            screen,
            color,
            world_to_screen(shape.x, shape.y, offset),
            round(shape.radius),
        )
    elif shape.kind == "ellipse":
        rect = pygame.Rect(
            round(shape.x - shape.rx - offset[0]),
            round(shape.y - shape.ry - offset[1]),
            round(shape.rx * 2),
            round(shape.ry * 2),
        )
        pygame.draw.ellipse(screen, color, rect)
    elif len(shape.points) >= 3:
        pygame.draw.polygon(screen, color, [world_to_screen(x, y, offset) for x, y in shape.points])
    elif len(shape.points) == 2:
        pygame.draw.line(
            screen,
            color,
            world_to_screen(shape.points[0][0], shape.points[0][1], offset),
            world_to_screen(shape.points[1][0], shape.points[1][1], offset),
            3,
        )


def draw_powerups(screen: pygame.Surface, font: pygame.font.Font, score: int) -> None:
    rects = powerup_button_rects()
    panel = pygame.Rect(WIDTH // 2 - 250, HEIGHT // 2 - 128, 500, 236)
    pygame.draw.rect(screen, (28, 28, 34), panel)
    pygame.draw.rect(screen, (220, 220, 230), panel, 2)

    title = font.render("Power Ups", True, (240, 240, 240))
    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.top + 12))

    for option in POWERUP_OPTIONS:
        rect = rects[option.id]
        affordable = score >= option.cost
        fill = (78, 78, 96) if affordable else (48, 48, 56)
        border = (240, 240, 240) if affordable else (120, 120, 128)
        pygame.draw.rect(screen, fill, rect)
        pygame.draw.rect(screen, border, rect, 2)
        label = font.render(option.label, True, border)
        cost = font.render(f"{option.cost} score", True, border)
        screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - 14))
        screen.blit(cost, (rect.centerx - cost.get_width() // 2, rect.centery + 10))


def draw_magazine(screen: pygame.Surface, magazine: MagazineState, now: float) -> None:
    center = (44, HEIGHT - 44)
    radius = 24
    rect = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
    pygame.draw.circle(screen, (70, 70, 76), center, radius, 2)
    draw_ammo(screen, center, radius, magazine.ammo)
    if magazine.reload_started_at:
        progress = reload_progress(magazine, now)
        pygame.draw.arc(
            screen,
            (240, 240, 240),
            rect,
            -math.pi / 2,
            -math.pi / 2 + math.tau * progress,
            4,
        )
        return

    count = max(1, magazine.weapon.magazine)
    remaining = max(0, magazine.remaining or 0)
    gap = 0.08
    segment = max(0.02, (math.tau / count) - gap)
    for index in range(count):
        start = -math.pi / 2 + index * math.tau / count
        color = (240, 240, 240) if index < remaining else (70, 70, 76)
        pygame.draw.arc(screen, color, rect, start, start + segment, 4)


def draw_ammo(screen: pygame.Surface, center: tuple[int, int], radius: int, ammo: int) -> None:
    strip_width = 7
    strip_height = 9
    strip_gap = 3
    count = 5
    x = center[0] + radius + 8
    top = center[1] - ((count * strip_height) + ((count - 1) * strip_gap)) // 2
    remaining = max(0, ammo)
    empty_count = max(0, count - remaining)
    for index in range(count):
        y = top + index * (strip_height + strip_gap)
        color = (70, 70, 76) if index < empty_count else (240, 240, 240)
        draw_cracked_ammo_cell(screen, pygame.Rect(x, y, strip_width, strip_height), color)


def draw_cracked_ammo_cell(screen: pygame.Surface, rect: pygame.Rect, color: tuple[int, int, int]) -> None:
    pygame.draw.line(screen, color, rect.topleft, (rect.right - 2, rect.top), 2)
    pygame.draw.line(screen, color, (rect.right - 1, rect.top + 1), (rect.right - 1, rect.bottom - 3), 2)
    pygame.draw.line(screen, color, (rect.right - 2, rect.bottom - 1), (rect.left + 2, rect.bottom - 1), 2)
    pygame.draw.line(screen, color, (rect.left, rect.bottom - 3), (rect.left, rect.top + 2), 2)
    pygame.draw.line(screen, color, (rect.left + 2, rect.top + 2), (rect.right - 3, rect.bottom - 3), 1)
