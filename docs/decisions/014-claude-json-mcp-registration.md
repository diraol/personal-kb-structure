# ADR-014: MCP Registration via ~/.claude.json, Not ~/.claude/settings.json

**Status:** Accepted  
**Date:** 2026-06-06

## Context

The original install script added the kb MCP server to `~/.claude/settings.json` under `mcpServers`. The server started and passed health checks locally but never appeared in Claude Code sessions — tools were not registered.

## Decision

Claude Code (v2.1+) reads **global** MCP server registrations from `~/.claude.json` (the internal state file), not from `~/.claude/settings.json`. The correct way to register a user-scoped MCP server is:

```bash
claude mcp add --scope user <name> [--transport http] <url-or-command>
```

This writes to `~/.claude.json`. The `settings.json` `mcpServers` key is unused for global servers and has been removed from `settings.snippet.json`. The install script now uses `claude mcp add -s user` exclusively.

## Consequences

- **+** MCP servers actually load in Claude Code sessions.
- **+** Using the official CLI (`claude mcp add`) is more robust than hand-editing JSON.
- **−** `~/.claude.json` is Claude Code's internal state file — not designed for hand-editing, may be overwritten on upgrades.
- **−** This behaviour is undocumented and was discovered by trial and error; future Claude Code versions may change it.
