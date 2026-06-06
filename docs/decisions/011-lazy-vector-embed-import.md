# ADR-011: Lazy Import of vector/embed Modules

**Status:** Accepted  
**Date:** 2026-05-11

## Context

`lancedb` (imported by `kb.vector`) takes ~2 seconds to import due to its Rust extension modules. Previously imported at module level in `kb/server.py` and `kb/search.py`, this caused the MCP server to take ~3.4s to respond to the MCP `initialize` handshake, likely exceeding Claude Code's startup timeout and causing the server to fail to register.

## Decision

Move `from kb import vector, embed` and `from kb import indexer` to lazy imports inside the functions that use them:
- `kb/search.py`: import `vector` and `embed` inside `hybrid_search()` within the try-block for semantic search.
- `kb/server.py`: import `indexer` inside the `kb_capture` handler.

This reduces MCP server startup from ~3.4s to ~1.2s.

## Consequences

- **+** MCP server starts fast enough to register within Claude Code's timeout.
- **+** FTS-only environments (no Ollama) never pay the lancedb import cost.
- **−** First call to `kb_search` (semantic) or `kb_capture` pays the import cost (~2s) once per process lifetime.
- **−** Import errors in vector/embed surface at call time, not at startup.
