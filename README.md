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
- Mouse aims the short indicator line from your dot
- Left click shoots a bullet toward the mouse

Each player has a random dot color and indicator color. The indicator length is fixed at `20` pixels. Bullet hits remove one health. Hit players blink for two seconds and are invulnerable while blinking. Dead players respawn after two seconds.

## Test and lint

```bash
uv run pytest
uv run ruff check .
```

## Release build 0.1.0

Build the local platform executable with PyInstaller:

```bash
uv sync --dev
uv run pyinstaller zozode.spec --clean --noconfirm
```

The executable is written to `dist/zozode` on Linux/macOS and `dist/zozode.exe` on Windows. The `assets/` directory is bundled into the executable.

Windows, Linux, and macOS release artifacts are built by the `Release builds` GitHub Actions workflow. Push a version tag such as `v0.1.0` to publish the platform executables as release assets:

- `zozode-0.1.0-win.exe`
- `zozode-0.1.0-linux`
- `zozode-0.1.0-mac`
