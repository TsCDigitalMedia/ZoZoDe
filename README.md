# ZoZoDe

A simple pixel game that can be played multiplayer over LAN.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
```

## Run

Start a server on the default UDP port `2806`:

```bash
uv run zozode
```

Join from another machine on the same LAN:

```bash
uv run zozode --join <server-ip>
```

Use a custom UDP port or host sword length when needed:

```bash
uv run zozode --port 2807 --max-length 180
uv run zozode --join <server-ip> --port 2807
```

## Controls

- `W` moves up
- `A` moves left
- `S` moves down
- `D` moves right
- Mouse aims the sword line from your dot

Each player has a random dot color and sword color. The host caps sword length with `--max-length`. A sword hit removes one health. Hit players blink for two seconds and are invulnerable while blinking. Dead players respawn after two seconds.

## Test and lint

```bash
uv run pytest
uv run ruff check .
```
