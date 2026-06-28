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

Use a custom UDP port when needed:

```bash
uv run zozode --port 2807
uv run zozode --join <server-ip> --port 2807
```

## Controls

- `W` moves up
- `A` moves left
- `S` moves down
- `D` moves right

Each joining client is assigned a random dot color by the server. Movement is sent over UDP.

## Test and lint

```bash
uv run pytest
uv run ruff check .
```
