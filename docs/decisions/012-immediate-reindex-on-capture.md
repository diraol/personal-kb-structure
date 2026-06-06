# ADR-012: Immediate Reindex on kb_capture

**Status:** Accepted  
**Date:** 2026-05-11

## Context

When the MCP `kb_capture` tool writes a new note, it could either wait for the background watcher to pick it up (eventually) or reindex the note immediately within the same call.

## Decision

After `kb_capture` writes the note file, it calls `indexer.reindex(paths=[target], with_embeddings=True)` synchronously before returning. This makes the note immediately searchable within the same Claude session.

## Consequences

- **+** Notes captured mid-session are searchable immediately — no watcher lag.
- **+** Consistent behaviour regardless of whether the watcher is running.
- **−** `kb_capture` is slower than a pure file write (adds ~1s for embedding).
- **−** The watcher will also detect the new file and reindex it (no-op due to mtime check, but wastes a cycle).
