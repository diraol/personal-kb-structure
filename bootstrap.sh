#!/usr/bin/env bash
# Bootstrap the kb vault on a fresh machine.
#
# This repo (personal-kb-structure) contains the infrastructure only.
# Vault notes live in a separate repo cloned into vault/ — supply it via
# --vault-repo or leave it out to start with an empty local vault.
#
# Steps:
#   1. uv sync           — install Python deps
#   2. Ollama check      — warn if missing or model not pulled
#   3. Vault setup       — clone vault repo into vault/, or init empty
#   4. kb-index --full   — build initial indexes
#   5. Claude wiring     — symlinks + settings merge
#   6. systemd watcher   — optional (prompts)
#
# Usage:
#   ./bootstrap.sh                                         # interactive, empty vault
#   ./bootstrap.sh --vault-repo git@github.com:org/repo    # clone vault from remote
#   ./bootstrap.sh --no-watcher                            # skip systemd step
#   ./bootstrap.sh --no-embeddings                         # skip Ollama / semantic indexing

set -euo pipefail

REPO="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
cd "$REPO"

WANT_WATCHER=1
WANT_EMBED=1
WANT_MCP_DAEMON=1
VAULT_REPO=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-watcher)     WANT_WATCHER=0 ;;
    --no-embeddings)  WANT_EMBED=0 ;;
    --no-mcp-daemon)  WANT_MCP_DAEMON=0 ;;
    --vault-repo)     shift; VAULT_REPO="${1:-}" ;;
    --vault-repo=*)   VAULT_REPO="${1#--vault-repo=}" ;;
    -h|--help)
      sed -n '2,20p' "$0"
      exit 0
      ;;
    *)
      echo "unknown flag: $1" >&2
      exit 2
      ;;
  esac
  shift
done

step() { printf '\n\033[1m[bootstrap] %s\033[0m\n' "$*" >&2; }
warn() { printf '\033[33m[bootstrap] %s\033[0m\n' "$*" >&2; }

step "1/6  uv sync"
if ! command -v uv >/dev/null; then
  warn "uv not installed. Install from https://docs.astral.sh/uv/ and retry."
  exit 1
fi
uv sync

step "2/6  Ollama check"
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

step "3/6  Vault setup"
VAULT_DIR="$REPO/vault"
if [[ -d "$VAULT_DIR/.git" ]]; then
  warn "vault/ is already a git repo — skipping vault setup (run git -C vault pull to update)."
elif [[ -n "$VAULT_REPO" ]]; then
  # Clone vault notes into vault/, keeping _meta/ which comes from this repo
  TMP_CLONE="$(mktemp -d)"
  git clone "$VAULT_REPO" "$TMP_CLONE"
  # Copy note dirs only (not .git, not anything that would overwrite _meta)
  for d in projects domains memory references; do
    [[ -d "$TMP_CLONE/$d" ]] && cp -r "$TMP_CLONE/$d" "$VAULT_DIR/"
  done
  [[ -f "$TMP_CLONE/.gitignore" ]] && cp "$TMP_CLONE/.gitignore" "$VAULT_DIR/.gitignore"
  rm -rf "$TMP_CLONE"
  # Re-init vault as its own repo pointing at the remote
  git -C "$VAULT_DIR" init -b main
  git -C "$VAULT_DIR" remote add origin "$VAULT_REPO"
  git -C "$VAULT_DIR" add .
  git -C "$VAULT_DIR" fetch origin main --depth=1 2>/dev/null || true
  git -C "$VAULT_DIR" reset --hard origin/main 2>/dev/null \
    || warn "Could not reset to origin/main — vault initialised from local copy."
  warn "Vault cloned from $VAULT_REPO"
else
  warn "No --vault-repo supplied. vault/ will contain only _meta/ (templates)."
  warn "To attach a vault later:  git -C vault init && git -C vault remote add origin <url>"
fi

step "4/6  Build indexes"
if (( WANT_EMBED )); then
  uv run kb-index --full
else
  uv run kb-index --full --no-embeddings
fi

step "5/6  Claude Code wiring"
"$REPO/claude-integration/install.sh"

step "6/6  Systemd services (watcher + MCP daemon)"
if (( WANT_WATCHER )) || (( WANT_MCP_DAEMON )); then
  if command -v systemctl >/dev/null && systemctl --user --version >/dev/null 2>&1; then
    "$REPO/systemd/install.sh"
  else
    warn "systemd --user not available; skipping service install."
    (( WANT_WATCHER ))    && warn "  Watcher:    uv run kb-watch  (run in a terminal)"
    (( WANT_MCP_DAEMON )) && warn "  MCP daemon: uv run kb-server --transport http --port 3333"
  fi
else
  warn "skipped systemd services (--no-watcher --no-mcp-daemon)"
fi

step "Done."
cat >&2 <<EOF

Next:
  - Restart Claude Code so the kb MCP server and hooks load.
  - Drop notes into vault/ — the watcher reindexes on save.
  - Use the kb-search / kb-capture / kb-consolidate skills, or the kb_* MCP tools.

Vault notes repo: ${VAULT_REPO:-"(none — initialise manually)"}
  git -C vault pull            pull latest notes
  git -C vault add . && git -C vault commit && git -C vault push
EOF
