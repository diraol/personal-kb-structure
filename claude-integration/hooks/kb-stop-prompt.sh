#!/usr/bin/env bash
# Stop hook: soft nudge to run kb-consolidate when sessions in the knowldege vault
# (or projects with .kb-project) wrap up. Stays silent for short / casual sessions.

set -uo pipefail

VAULT="${KB_VAULT:-$HOME/dev/knowldege/vault}"
cwd="${CLAUDE_PROJECT_DIR:-$PWD}"

# Only nudge inside the vault repo or a project that opts in via .kb-project
if [[ "$cwd" != "$(dirname "$VAULT")"* && ! -f "$cwd/.kb-project" ]]; then
  exit 0
fi

cat <<'EOF'
[kb] If this session produced decisions, gotchas, or learnings worth keeping, run /kb-consolidate before closing.
EOF
