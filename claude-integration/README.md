---
id: claude-integration-readme
type: meta
tags: [bootstrap, claude-code]
created: 2026-05-11
updated: 2026-05-11
---

# Claude Code integration

Everything Claude Code needs to use the kb vault — vendored here so a fresh
machine can bootstrap with `git clone && ./bootstrap.sh`.

## Layout

```
claude-integration/
├── skills/
│   ├── kb-search/SKILL.md       symlinked → ~/.claude/skills/kb-search
│   ├── kb-capture/SKILL.md      symlinked → ~/.claude/skills/kb-capture
│   └── kb-consolidate/SKILL.md  symlinked → ~/.claude/skills/kb-consolidate
├── hooks/
│   ├── kb-session-context.sh    symlinked → ~/.claude/hooks/kb-session-context.sh
│   └── kb-stop-prompt.sh        symlinked → ~/.claude/hooks/kb-stop-prompt.sh
├── settings.snippet.json        template merged into ~/.claude/settings.json
├── merge-settings.py            idempotent merger with timestamped backup
├── install.sh                   one-shot wiring (calls merge-settings.py)
└── README.md
```

## What `install.sh` does

1. **Symlinks** each skill folder and hook file into `~/.claude/{skills,hooks}/`.
   Existing files at the target are moved aside as `.bak-pre-kb-<timestamp>`.
2. **Merges** `settings.snippet.json` into `~/.claude/settings.json`:
   - `mcpServers.kb` is set/overwritten (so updates to the server command apply).
   - Hook entries are appended only if the same `command` isn't already wired.
   - A timestamped backup of `settings.json` is written before any change.

Idempotent — safe to re-run on every git pull.

## Usage

```bash
./claude-integration/install.sh           # apply
./claude-integration/install.sh --dry-run # preview
```

## What gets injected

`mcpServers.kb` (so Claude Code spawns the local MCP server):
```json
{
  "command": "$HOME/.local/bin/uv",
  "args": ["run", "--project", "<repo-path>", "kb-server"]
}
```

`hooks.SessionStart` / `hooks.Stop` — point to the symlinked scripts under
`~/.claude/hooks/`.

## After install

Restart Claude Code. The new MCP server and hooks load on the next session.

To verify:
- `claude --debug` shows `kb` in the mcpServers list at startup.
- `cd ~/kb && claude` should inject the project index via SessionStart.

## Uninstalling

```bash
# Remove symlinks (existing backups untouched)
rm ~/.claude/skills/kb-{search,capture,consolidate}
rm ~/.claude/hooks/kb-{session-context,stop-prompt}.sh

# Remove mcpServers.kb and the hooks entries from ~/.claude/settings.json
# (or restore from a .bak-pre-kb-* file)
```
