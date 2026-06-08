#!/usr/bin/env bash
# Wire the kb vault into Claude Code:
#   - symlink skills/hooks from the repo into ~/.claude/{skills,hooks}/
#   - merge MCP server + hook entries into ~/.claude/settings.json (with backup)
#
# Idempotent: safe to re-run.
#
# Usage:
#   ./claude-integration/install.sh           # do it
#   ./claude-integration/install.sh --dry-run # show the plan, change nothing

set -euo pipefail

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

REPO="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
CLAUDE_DIR="${CLAUDE_HOME:-$HOME/.claude}"
SKILLS_DST="$CLAUDE_DIR/skills"
HOOKS_DST="$CLAUDE_DIR/hooks"

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

log "[kb-install] repo: $REPO"
log "[kb-install] target: $CLAUDE_DIR"
log

log "[skills]"
for d in "$REPO"/claude-integration/skills/*/; do
  name="$(basename "$d")"
  ensure_link "$d" "$SKILLS_DST/$name"
done

log
log "[hooks]"
for f in "$REPO"/agent-integration/hooks/claude/*.sh; do
  name="$(basename "$f")"
  chmod +x "$f"
  ensure_link "$f" "$HOOKS_DST/$name"
done

log
log "[MCP server]"
KB_MCP_PORT="${KB_MCP_PORT:-3333}"
_HAS_SYSTEMD=0
command -v systemctl >/dev/null 2>&1 && systemctl --user --version >/dev/null 2>&1 && _HAS_SYSTEMD=1

if (( _HAS_SYSTEMD )); then
  # HTTP mode: connect to the persistent daemon
  MCP_URL="http://127.0.0.1:${KB_MCP_PORT}/mcp"
  if (( DRY_RUN )); then
    log "  plan  claude mcp add -s user --transport http kb $MCP_URL"
  else
    claude mcp remove -s user kb 2>/dev/null || true
    claude mcp add -s user --transport http kb "$MCP_URL" 2>&1 | sed 's/^/  /' || true
    log "  ok    kb MCP server registered as HTTP (url: $MCP_URL)"
  fi
else
  # Fallback: stdio mode (no systemd — containers, WSL without systemd, etc.)
  UV_BIN="$(command -v uv || true)"
  if [[ -z "$UV_BIN" ]]; then
    log "  warn  uv not found in PATH; skipping claude mcp add"
    log "        Run manually: claude mcp add -s user kb -- <path-to-uv> run --project $REPO kb-server"
  elif (( DRY_RUN )); then
    log "  plan  claude mcp add -s user kb -- $UV_BIN run --project $REPO kb-server  (stdio fallback)"
  else
    claude mcp remove -s user kb 2>/dev/null || true
    claude mcp add -s user kb -- "$UV_BIN" run --project "$REPO" kb-server 2>&1 \
      | sed 's/^/  /' || true
    log "  ok    kb MCP server registered as stdio (systemd unavailable)"
  fi
fi

log
log "[settings.json hooks]"
if (( DRY_RUN )); then
  python3 "$REPO/claude-integration/merge-settings.py" --repo "$REPO" --dry-run
else
  python3 "$REPO/claude-integration/merge-settings.py" --repo "$REPO"
fi

log
log "[CLAUDE.md]"
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
SNIPPET="$REPO/claude-integration/claude.md.snippet"
SENTINEL="## Knowledge Base (kb MCP)"
if [[ -f "$SNIPPET" ]]; then
  if grep -qF "$SENTINEL" "$CLAUDE_MD" 2>/dev/null; then
    log "  ok    kb section already present in $CLAUDE_MD"
  elif (( DRY_RUN )); then
    log "  plan  append kb section to $CLAUDE_MD"
  else
    printf '\n' >> "$CLAUDE_MD"
    cat "$SNIPPET" >> "$CLAUDE_MD"
    log "  added kb section to $CLAUDE_MD"
  fi
else
  warn "claude.md.snippet not found, skipping CLAUDE.md merge"
fi

log
log "[done]  Restart Claude Code to load the kb MCP server and hooks."
log "        Verify:  claude --debug    (look for 'kb' in mcpServers)"
