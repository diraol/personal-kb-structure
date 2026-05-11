#!/usr/bin/env bash
# Bootstrap the knowldege vault on a fresh machine.
#
# Steps:
#   1. uv sync           — install Python deps
#   2. ollama check      — warn if missing or model not pulled
#   3. kb-index --full   — build initial indexes
#   4. Claude wiring     — symlinks + settings merge
#   5. systemd watcher   — optional (prompts)
#
# Usage:
#   ./bootstrap.sh                  # interactive
#   ./bootstrap.sh --no-watcher     # skip systemd step
#   ./bootstrap.sh --no-embeddings  # skip Ollama / semantic indexing

set -euo pipefail

REPO="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
cd "$REPO"

WANT_WATCHER=1
WANT_EMBED=1
for arg in "$@"; do
  case "$arg" in
    --no-watcher) WANT_WATCHER=0 ;;
    --no-embeddings) WANT_EMBED=0 ;;
    -h|--help)
      sed -n '2,15p' "$0"
      exit 0
      ;;
    *)
      echo "unknown flag: $arg" >&2
      exit 2
      ;;
  esac
done

step() { printf '\n\033[1m[bootstrap] %s\033[0m\n' "$*" >&2; }
warn() { printf '\033[33m[bootstrap] %s\033[0m\n' "$*" >&2; }

step "1/5  uv sync"
if ! command -v uv >/dev/null; then
  warn "uv not installed. Install from https://docs.astral.sh/uv/ and retry."
  exit 1
fi
uv sync

step "2/5  Ollama check"
if (( WANT_EMBED )); then
  if ! command -v ollama >/dev/null; then
    warn "ollama not found — install from https://ollama.com/install.sh, then:"
    warn "    ollama pull nomic-embed-text"
    warn "Proceeding with FTS-only indexing for now."
    WANT_EMBED=0
  elif ! ollama list 2>/dev/null | grep -q '^nomic-embed-text'; then
    warn "model nomic-embed-text not pulled. Running: ollama pull nomic-embed-text"
    ollama pull nomic-embed-text || { warn "pull failed; FTS-only mode."; WANT_EMBED=0; }
  fi
fi

step "3/5  Build indexes"
if (( WANT_EMBED )); then
  uv run kb-index --full
else
  uv run kb-index --full --no-embeddings
fi

step "4/5  Claude Code wiring"
"$REPO/claude-integration/install.sh"

step "5/5  Watcher daemon"
if (( WANT_WATCHER )); then
  if command -v systemctl >/dev/null && systemctl --user --version >/dev/null 2>&1; then
    "$REPO/systemd/install.sh"
  else
    warn "systemd --user not available; skipping watcher install."
    warn "You can still run: uv run kb-watch (in a terminal)"
  fi
else
  warn "skipped watcher (--no-watcher)"
fi

step "Done."
cat >&2 <<EOF

Next:
  - Restart Claude Code so the kb MCP server and hooks load.
  - Drop notes into vault/ — the watcher reindexes on save.
  - Use the kb-search / kb-capture / kb-consolidate skills, or the kb_* MCP tools.
EOF
