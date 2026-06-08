#!/usr/bin/env bash
# Wire the kb vault into Codex:
#   - symlink hooks from the repo into ~/.codex/hooks/
#   - merge kb hook entries into ~/.codex/hooks.json
#   - register kb MCP server
#
# Idempotent: safe to re-run.
#
# Usage:
#   ./agent-integration/install-codex.sh           # do it
#   ./agent-integration/install-codex.sh --dry-run # show the plan, change nothing

set -euo pipefail

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

REPO="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
HOOKS_DST="$CODEX_DIR/hooks"

log() { printf '%s\n' "$@" >&2; }

ensure_link() {
  local src="${1%/}" dst="$2"
  if [[ -L "$dst" && "$(readlink "$dst")" == "$src" ]]; then
    log "  ok    $dst → $src"
    return
  fi
  if (( DRY_RUN )); then
    log "  plan  $dst → $src"
    return
  fi
  mkdir -p "$(dirname "$dst")"
  if [[ -e "$dst" || -L "$dst" ]]; then
    mv "$dst" "$dst.bak-pre-kb-$(date +%Y%m%d-%H%M%S)"
    log "  back  $dst (existing moved aside)"
  fi
  ln -s "$src" "$dst"
  log "  link  $dst → $src"
}

log "[kb-install-codex] repo: $REPO"
log "[kb-install-codex] target: $CODEX_DIR"
log

log "[hooks]"
for f in "$REPO"/agent-integration/hooks/codex/*.py; do
  name="$(basename "$f")"
  chmod +x "$f"
  ensure_link "$f" "$HOOKS_DST/$name"
done

log
log "[hooks.json]"
HOOKS_JSON="$CODEX_DIR/hooks.json"
if (( DRY_RUN )); then
  python3 "$REPO/agent-integration/merge-codex-hooks.py" \
    --repo "$REPO" --hooks-json "$HOOKS_JSON" --dry-run
else
  python3 "$REPO/agent-integration/merge-codex-hooks.py" \
    --repo "$REPO" --hooks-json "$HOOKS_JSON"
fi

log
log "[MCP server]"
KB_MCP_PORT="${KB_MCP_PORT:-3333}"
_HAS_SYSTEMD=0
command -v systemctl >/dev/null 2>&1 && systemctl --user --version >/dev/null 2>&1 && _HAS_SYSTEMD=1

if (( _HAS_SYSTEMD )); then
  MCP_URL="http://127.0.0.1:${KB_MCP_PORT}/mcp"
  if (( DRY_RUN )); then
    log "  plan  codex mcp add kb --url $MCP_URL"
  else
    codex mcp remove kb 2>/dev/null || true
    codex mcp add kb --url "$MCP_URL" 2>&1 | sed 's/^/  /' || true
    log "  ok    kb MCP registered as HTTP (url: $MCP_URL)"
  fi
else
  UV_BIN="$(command -v uv || true)"
  if [[ -z "$UV_BIN" ]]; then
    log "  warn  uv not found in PATH; skipping codex mcp add"
    log "        Run manually: codex mcp add kb -- <path-to-uv> run --project $REPO kb-server"
  elif (( DRY_RUN )); then
    log "  plan  codex mcp add kb -- $UV_BIN run --project $REPO kb-server  (stdio fallback)"
  else
    codex mcp remove kb 2>/dev/null || true
    codex mcp add kb -- "$UV_BIN" run --project "$REPO" kb-server 2>&1 | sed 's/^/  /' || true
    log "  ok    kb MCP registered as stdio (systemd unavailable)"
  fi
fi

log
log "[done]  Restart Codex to load the kb MCP server and hooks."
log "        Note: Codex will prompt to trust new/changed hooks on first run."
