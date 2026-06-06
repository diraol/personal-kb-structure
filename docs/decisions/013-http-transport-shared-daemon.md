# ADR-013: HTTP Transport for MCP Server (Shared Daemon)

**Status:** Accepted  
**Date:** 2026-06-06

## Context

The MCP server was originally configured as a stdio transport — Claude Code spawned a new `kb-server` process per session. With multiple simultaneous Claude sessions (a common usage pattern), this created 3-5 independent processes each loading lancedb (~130MB each) into memory.

## Decision

Switch to **StreamableHTTP transport** (MCP 2025-11 spec) running as a persistent systemd user service. A single `kb-server --transport http --port 3333` process handles all sessions. Claude Code and other tools (Codex, GitHub Copilot) connect via `http://127.0.0.1:3333/mcp`.

The stdio mode is preserved as a fallback for environments without systemd (containers, WSL without systemd).

`StreamableHTTPSessionManager` is used with `stateless=False` to maintain per-client session state. A `/health` endpoint enables lightweight liveness probes.

## Consequences

- **+** Single process regardless of how many sessions or tools are connected.
- **+** Eliminates ~130MB × N-sessions memory overhead.
- **+** All tools (Claude Code, Codex, Copilot) share the same server via a URL.
- **+** Server persists across session restarts; no startup latency per session.
- **−** Requires systemd --user (not available in all environments).
- **−** If the daemon crashes, all sessions lose MCP until it restarts (5s backoff).
- **−** Port 3333 must be free; conflicts require manual `KB_MCP_PORT` override.
