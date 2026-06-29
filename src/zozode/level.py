from __future__ import annotations

import math
import random
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from zozode.assets import ASSETS_DIR
from zozode.geometry import clamp

_NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
_PATH_TOKEN_RE = re.compile(rf"[MmLlHhVvZz]|{_NUMBER}")


@dataclass(frozen=True, slots=True)
class LevelShape:
    kind: str
    points: tuple[tuple[float, float], ...] = ()
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    radius: float = 0.0
    rx: float = 0.0
    ry: float = 0.0
    color: tuple[int, int, int] | None = None

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        if self.kind == "rect":
            return self.x, self.y, self.x + self.width, self.y + self.height
        if self.kind == "circle":
            return (
                self.x - self.radius,
                self.y - self.radius,
                self.x + self.radius,
                self.y + self.radius,
            )
        if self.kind == "ellipse":
            return self.x - self.rx, self.y - self.ry, self.x + self.rx, self.y + self.ry
        if not self.points:
            return 0.0, 0.0, 0.0, 0.0
        xs = [point[0] for point in self.points]
        ys = [point[1] for point in self.points]
        return min(xs), min(ys), max(xs), max(ys)

    def contains(self, x: float, y: float) -> bool:
        if self.kind == "rect":
            return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height
        if self.kind == "circle":
            return math.hypot(x - self.x, y - self.y) <= self.radius
        if self.kind == "ellipse":
            if self.rx == 0 or self.ry == 0:
                return False
            return ((x - self.x) / self.rx) ** 2 + ((y - self.y) / self.ry) ** 2 <= 1
        if len(self.points) < 3:
            return False
        inside = False
        j = len(self.points) - 1
        for i, point in enumerate(self.points):
            xi, yi = point
            xj, yj = self.points[j]
            if (yi > y) != (yj > y):
                cross_x = ((xj - xi) * (y - yi) / (yj - yi)) + xi
                if x < cross_x:
                    inside = not inside
            j = i
        return inside

    def random_point(self) -> tuple[float, float]:
        if self.kind == "circle":
            angle = random.uniform(0, math.tau)
            radius = self.radius * math.sqrt(random.random())
            return self.x + math.cos(angle) * radius, self.y + math.sin(angle) * radius
        if self.kind == "ellipse":
            angle = random.uniform(0, math.tau)
            radius = math.sqrt(random.random())
            return (
                self.x + math.cos(angle) * self.rx * radius,
                self.y + math.sin(angle) * self.ry * radius,
            )
        if len(self.points) == 2:
            amount = random.random()
            start, end = self.points
            return start[0] + (end[0] - start[0]) * amount, start[1] + (end[1] - start[1]) * amount
        min_x, min_y, max_x, max_y = self.bounds
        for _ in range(100):
            x = random.uniform(min_x, max_x)
            y = random.uniform(min_y, max_y)
            if self.contains(x, y):
                return x, y
        return (min_x + max_x) / 2, (min_y + max_y) / 2


@dataclass(frozen=True, slots=True)
class Level:
    width: float
    height: float
    ground: tuple[LevelShape, ...]
    enemy_spawns: tuple[LevelShape, ...]
    player_spawns: tuple[LevelShape, ...]
    obstacles: tuple[LevelShape, ...] = ()
    textures: tuple[LevelShape, ...] = ()
    texture_svg: str | None = None

    def contains_ground(self, x: float, y: float) -> bool:
        return any(shape.contains(x, y) for shape in self.ground)

    def contains_obstacle(self, x: float, y: float) -> bool:
        return any(shape.contains(x, y) for shape in self.obstacles)

    def can_walk(self, x: float, y: float, radius: float) -> bool:
        x = clamp(x, radius, self.width - radius)
        y = clamp(y, radius, self.height - radius)
        return self.contains_ground(x, y) and not self.contains_obstacle(x, y)

    def random_player_spawn(self, radius: float) -> tuple[float, float]:
        return self._random_spawn(self.player_spawns or self.ground, radius)

    def random_enemy_spawn(self, radius: float) -> tuple[float, float]:
        return self._random_spawn(self.enemy_spawns or self.ground, radius)

    def in_bounds(self, x: float, y: float, margin: float = 0.0) -> bool:
        return -margin <= x <= self.width + margin and -margin <= y <= self.height + margin

    def _random_spawn(self, shapes: tuple[LevelShape, ...], radius: float) -> tuple[float, float]:
        if not shapes:
            return self.width / 2, self.height / 2
        for _ in range(100):
            x, y = shapes[random.randrange(len(shapes))].random_point()
            x = clamp(x, radius, self.width - radius)
            y = clamp(y, radius, self.height - radius)
            if self.can_walk(x, y, radius) or shapes is self.ground:
                return x, y
        x, y = shapes[random.randrange(len(shapes))].random_point()
        return clamp(x, radius, self.width - radius), clamp(y, radius, self.height - radius)


def load_default_level() -> Level:
    return load_level(ASSETS_DIR / "Levels" / "Hallway.svg")


def load_level(path: Path) -> Level:
    root = ET.parse(path).getroot()
    width, height = _svg_size(root)
    ground = tuple(_layer_shapes(root, "ground"))
    enemy_spawns = tuple(_layer_shapes(root, "enemySpawn"))
    player_spawns = tuple(_layer_shapes(root, "playerSpawn"))
    obstacles = tuple(_layer_shapes(root, "obstacle"))
    textures = tuple(_texture_shapes(root))
    texture_svg = _texture_svg(root)
    return Level(width, height, ground, enemy_spawns, player_spawns, obstacles, textures, texture_svg)


def _svg_size(root: ET.Element) -> tuple[float, float]:
    view_box = root.attrib.get("viewBox")
    if view_box:
        values = [float(value) for value in view_box.replace(",", " ").split()]
        if len(values) == 4:
            return values[2], values[3]
    return _length(root.attrib.get("width", "1600")), _length(root.attrib.get("height", "1200"))


def _layer_shapes(root: ET.Element, layer_id: str) -> list[LevelShape]:
    shapes: list[LevelShape] = []
    for element in root.iter():
        if element.attrib.get("id") != layer_id:
            continue
        for child in list(element):
            shape = _shape_from_element(child)
            if shape is not None:
                shapes.append(shape)
        return shapes
    return shapes


def _texture_shapes(root: ET.Element) -> list[LevelShape]:
    logic_layer_ids = {"ground", "enemySpawn", "playerSpawn", "obstacle"}
    shapes: list[LevelShape] = []
    for layer in _svg_layers(root):
        if layer.attrib.get("id") in logic_layer_ids:
            continue
        for child in list(layer):
            shape = _shape_from_element(child)
            if shape is not None:
                shapes.append(shape)
    return shapes


def _texture_svg(root: ET.Element) -> str | None:
    logic_layer_ids = {"ground", "enemySpawn", "playerSpawn", "obstacle"}
    has_texture_layer = any(
        layer.attrib.get("id") not in logic_layer_ids for layer in _svg_layers(root)
    )
    if not has_texture_layer:
        return None
    for parent in root.iter():
        for child in list(parent):
            if child.attrib.get("id") in logic_layer_ids:
                parent.remove(child)
    return ET.tostring(root, encoding="unicode")


def _svg_layers(root: ET.Element) -> list[ET.Element]:
    return [
        element
        for element in root.iter()
        if _tag_name(element.tag) == "g" and (element.attrib.get("id") or "")
    ]


def _shape_from_element(element: ET.Element) -> LevelShape | None:
    tag = _tag_name(element.tag)
    color = _fill_color(element.attrib.get("style", ""))
    if tag == "rect":
        return LevelShape(
            kind="rect",
            x=_length(element.attrib.get("x", "0")),
            y=_length(element.attrib.get("y", "0")),
            width=_length(element.attrib.get("width", "0")),
            height=_length(element.attrib.get("height", "0")),
            color=color,
        )
    if tag == "circle":
        return LevelShape(
            kind="circle",
            x=_length(element.attrib.get("cx", "0")),
            y=_length(element.attrib.get("cy", "0")),
            radius=_length(element.attrib.get("r", "0")),
            color=color,
        )
    if tag == "ellipse":
        return LevelShape(
            kind="ellipse",
            x=_length(element.attrib.get("cx", "0")),
            y=_length(element.attrib.get("cy", "0")),
            rx=_length(element.attrib.get("rx", "0")),
            ry=_length(element.attrib.get("ry", "0")),
            color=color,
        )
    if tag in {"polygon", "polyline"}:
        points = _parse_points(element.attrib.get("points", ""))
        if points:
            return LevelShape(kind="polygon", points=tuple(points), color=color)
    if tag == "path":
        points = _parse_path_points(element.attrib.get("d", ""))
        if points:
            return LevelShape(kind="path", points=tuple(points), color=color)
    return None


def _tag_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _length(value: str) -> float:
    match = re.match(_NUMBER, value.strip())
    return float(match.group(0)) if match else 0.0


def _fill_color(style: str) -> tuple[int, int, int] | None:
    match = re.search(r"(?:^|;)\s*fill\s*:\s*#([0-9a-fA-F]{6})", style)
    if not match:
        return None
    value = match.group(1)
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _parse_points(payload: str) -> list[tuple[float, float]]:
    values = [float(value) for value in re.findall(_NUMBER, payload)]
    return list(zip(values[0::2], values[1::2], strict=False))


def _parse_path_points(payload: str) -> list[tuple[float, float]]:
    tokens = _PATH_TOKEN_RE.findall(payload)
    points: list[tuple[float, float]] = []
    index = 0
    command = ""
    current = (0.0, 0.0)
    start = (0.0, 0.0)
    while index < len(tokens):
        token = tokens[index]
        if re.fullmatch(r"[A-Za-z]", token):
            command = token
            index += 1
        if command in {"M", "m", "L", "l"} and index + 1 < len(tokens):
            x = float(tokens[index])
            y = float(tokens[index + 1])
            index += 2
            if command.islower():
                x += current[0]
                y += current[1]
            current = (x, y)
            if command in {"M", "m"} and not points:
                start = current
            points.append(current)
            if command in {"M", "m"}:
                command = "l" if command == "m" else "L"
        elif command in {"H", "h"} and index < len(tokens):
            x = float(tokens[index])
            index += 1
            if command == "h":
                x += current[0]
            current = (x, current[1])
            points.append(current)
        elif command in {"V", "v"} and index < len(tokens):
            y = float(tokens[index])
            index += 1
            if command == "v":
                y += current[1]
            current = (current[0], y)
            points.append(current)
        elif command in {"Z", "z"}:
            points.append(start)
        else:
            index += 1
    return points


DEFAULT_LEVEL = load_default_level()
