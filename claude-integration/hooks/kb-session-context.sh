#!/usr/bin/env bash
# SessionStart hook: inject the current project's vault _index.md as context.
#
# Resolves the project by:
#   1. CLAUDE_PROJECT_DIR / cwd basename → vault/projects/<basename>/_index.md
#   2. .kb-project file in cwd → contains the project slug
# Prints the index content to stdout (Claude Code injects stdout as additionalContext).
# Silent if no match.

set -uo pipefail

VAULT="${KB_VAULT:-$HOME/dev/knowldege/vault}"
[[ -d "$VAULT/projects" ]] || exit 0

cwd="${CLAUDE_PROJECT_DIR:-$PWD}"
slug=""

if [[ -f "$cwd/.kb-project" ]]; then
  slug="$(head -1 "$cwd/.kb-project" | tr -d '[:space:]')"
fi

if [[ -z "$slug" ]]; then
  slug="$(basename "$cwd")"
fi

idx="$VAULT/projects/$slug/_index.md"
[[ -f "$idx" ]] || exit 0

cat <<EOF
<knowldege-project-context project="$slug" source="$idx">
$(cat "$idx")
</knowldege-project-context>

(Tip: use kb_search / kb-search skill for deeper retrieval. Use kb_capture / kb-capture to persist new learnings.)
EOF
