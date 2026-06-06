#!/usr/bin/env bash
# Install kb systemd user units: kb-watch and kb-mcp-server.
set -euo pipefail

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
REPO="$(dirname "$SCRIPT_DIR")"
DEST_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
LOGS_DIR="$REPO/.logs"

# Resolve uv to the real binary (not a pyenv shim) so systemd can use it.
# pyenv shims require PYENV_ROOT/PATH setup that systemd --user doesn't have.
_resolve_real_uv() {
  local candidate
  candidate="$(command -v uv 2>/dev/null || true)"
  [[ -z "$candidate" ]] && return 1

  # Not a shim — use as-is
  [[ "$candidate" != *pyenv/shims/* ]] && { echo "$candidate"; return 0; }

  # It's a pyenv shim: search pyenv versions for a real uv binary
  local pyenv_root
  pyenv_root="${PYENV_ROOT:-$HOME/.pyenv}"
  local found
  found="$(find "$pyenv_root/versions" -name uv -type f 2>/dev/null | \
    grep -v '/envs/' | sort -V | tail -1)"
  [[ -n "$found" ]] && { echo "$found"; return 0; }

  # Fallback: include envs too
  found="$(find "$pyenv_root/versions" -name uv -type f 2>/dev/null | sort -V | tail -1)"
  [[ -n "$found" ]] && { echo "$found"; return 0; }

  return 1
}

UV_BIN="$(_resolve_real_uv || true)"
if [[ -z "$UV_BIN" ]]; then
  echo "ERROR: uv not found in PATH or pyenv versions" >&2
  exit 1
fi
echo "[systemd] uv resolved to: $UV_BIN"

mkdir -p "$DEST_DIR" "$LOGS_DIR"

install_unit() {
  local name="$1"
  local src="$SCRIPT_DIR/${name}.service"
  local dest="$DEST_DIR/${name}.service"
  # Substitute @UV_BIN@ placeholder with the resolved path
  sed "s|@UV_BIN@|${UV_BIN}|g" "$src" > "$dest"
  echo "[systemd] installed $dest"
}

# --- kb-watch ---
install_unit kb-watch
systemctl --user daemon-reload
systemctl --user enable --now kb-watch.service
echo "[kb-watch] enabled and started."

# --- kb-mcp-server ---
install_unit kb-mcp-server
systemctl --user daemon-reload
systemctl --user enable --now kb-mcp-server.service
echo "[kb-mcp-server] enabled and started."

# Wait for kb-mcp-server to bind (up to 10s)
KB_MCP_PORT="${KB_MCP_PORT:-3333}"
echo -n "[kb-mcp-server] waiting for HTTP on :${KB_MCP_PORT} ..."
for i in $(seq 1 10); do
  if curl -sf "http://127.0.0.1:${KB_MCP_PORT}/health" >/dev/null 2>&1; then
    echo " ready."
    break
  fi
  echo -n "."
  sleep 1
done
if ! curl -sf "http://127.0.0.1:${KB_MCP_PORT}/health" >/dev/null 2>&1; then
  echo ""
  echo "WARNING: kb-mcp-server did not respond within 10s."
  echo "  Check logs: tail -f $LOGS_DIR/kb-mcp-server.log"
fi

echo
echo "Services installed. Useful commands:"
echo "  systemctl --user status kb-watch kb-mcp-server"
echo "  tail -f $LOGS_DIR/kb-mcp-server.log"
echo "  systemctl --user disable --now kb-watch kb-mcp-server"
