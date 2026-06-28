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

Start the UDP server:

```bash
uv run zozode-server
```

Run the UDP client:

```bash
uv run zozode
```

Send a custom client message:

```bash
uv run zozode "hello from client"
```

Use LAN binding when another machine needs to connect:

```bash
uv run zozode-server --host 0.0.0.0 --port 9999
uv run zozode "hello over LAN" --host <server-ip> --port 9999
```

Compatibility commands are also available:

```bash
uv run zozode server
uv run zozode client "hello"
```

## Test and lint

```bash
uv run pytest
uv run ruff check .
```

## Project layout

```text
src/zozode/
  __init__.py      package metadata
  client.py        client entrypoint for `uv run zozode`
  server.py        server entrypoint for `uv run zozode-server`
  cli.py           compatibility command router
  config.py        UDP configuration model
  udp.py           UDP send/server primitives
tests/
  test_config.py   config tests
  test_entrypoints.py entrypoint parser tests
main.py            compatibility wrapper
```
