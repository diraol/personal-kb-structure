# ADR-017: Systemd --user Units for Background Services

**Status:** Accepted  
**Date:** 2026-05-11

## Context

Two long-running processes are needed: the file watcher (`kb-watch`) for incremental reindexing, and the MCP HTTP server (`kb-mcp-server`) for shared tool access. These need to start on login and restart on failure.

## Decision

Use **systemd user units** (`systemctl --user`) for both services. Units are stored in the repo under `systemd/` as templates with `@UV_BIN@` placeholder. The `systemd/install.sh` script:
1. Resolves the real `uv` binary path (bypassing pyenv shims which don't work without the user environment).
2. Substitutes `@UV_BIN@` before copying to `~/.config/systemd/user/`.
3. Enables both units with `WantedBy=default.target`.

Logs go to `<KB_DIR>/.logs/` (gitignored). The install script falls back gracefully if `systemctl --user` is unavailable, printing manual-run instructions instead.

## Consequences

- **+** Services survive session restarts and reboot automatically on login.
- **+** `Restart=on-failure` handles crashes without user intervention.
- **+** Standard systemd tooling for status/logs (`journalctl`, `systemctl status`).
- **−** Requires systemd --user support — not available in Docker containers or WSL without systemd.
- **−** pyenv shims don't work in systemd's environment; the install script must resolve the real binary.
- **−** Users on non-systemd Linux (Alpine, Void with runit, macOS) need a different approach (launchd, runit, manual).
