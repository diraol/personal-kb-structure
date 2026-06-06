# kb — Technical Plan

Feature Branch: `main`  
Created: 2026-06-06  
Status: Active  
Spec: [docs/spec.md](spec.md)  
Constitution: [docs/constitution.md](constitution.md)

---

## Summary

kb is a Python application that:
1. Maintains a hybrid search index (FTS5 + LanceDB vectors) over a markdown vault.
2. Exposes search and capture tools via an MCP server.
3. Integrates with Claude Code via MCP, skills, and session hooks.
4. Runs as a persistent HTTP daemon shared across multiple AI sessions.

---

## Technical Context

| Aspect | Choice |
|--------|--------|
| Language | Python 3.11+ |
| Package manager | uv |
| MCP SDK | `mcp>=1.9.0` |
| Keyword search | SQLite FTS5 |
| Vector store | LanceDB |
| Embeddings | Ollama (`nomic-embed-text`, 768-dim) |
| HTTP server | uvicorn + Starlette |
| MCP transport | StreamableHTTP (primary), stdio (fallback) |
| Process management | systemd --user |
| Note format | CommonMark markdown + YAML frontmatter |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  AI Tools (Claude Code, Codex, Copilot)                     │
│  connect via HTTP to http://127.0.0.1:3333/mcp              │
└─────────────────┬───────────────────────────────────────────┘
                  │ MCP StreamableHTTP
┌─────────────────▼───────────────────────────────────────────┐
│  kb-server (systemd user unit, persistent daemon)           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  MCP Tools: kb_search, kb_get, kb_recent,              │ │
│  │             kb_related, kb_capture, kb_list_projects   │ │
│  └──────────────┬──────────────────────┬──────────────────┘ │
│                 │                      │                     │
│  ┌──────────────▼──────┐  ┌────────────▼──────────────────┐ │
│  │  kb.fts             │  │  kb.search (hybrid)           │ │
│  │  SQLite FTS5        │  │  kb.vector (LanceDB)          │ │
│  │  index/fts.sqlite   │  │  kb.embed (Ollama)            │ │
│  └─────────────────────┘  │  index/vectors.lance/         │ │
│                           └───────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                  ▲ reads                ▲ reindexes on save
┌─────────────────┴───────────────────────────────────────────┐
│  vault/ (separate git repo)                                 │
│  ├── projects/{slug}/  (project-scoped notes)               │
│  ├── domains/          (domain knowledge)                   │
│  ├── memory/           (cross-project facts, decisions)     │
│  ├── references/       (external resource pointers)         │
│  └── _meta/            (templates, schema — in structure)   │
└──────────────────────────────────────────────────────────────┘
                              ▲
┌─────────────────────────────┴───────────────────────────────┐
│  kb-watch (systemd user unit)                               │
│  watchfiles with 800ms debounce → kb-index incremental      │
└──────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
kb/                          # structure repo
├── kb/                      # Python package
│   ├── server.py            # MCP server (stdio + HTTP modes)
│   ├── cli.py               # kb-index, kb-search, kb-new, kb-watch
│   ├── search.py            # hybrid RRF search
│   ├── fts.py               # FTS5 operations
│   ├── vector.py            # LanceDB operations
│   ├── embed.py             # Ollama embedding client
│   ├── indexer.py           # incremental reindex logic
│   ├── chunk.py             # H2 + sliding window chunking
│   ├── frontmatter.py       # Note parsing and validation
│   ├── search_helpers.py    # FTS query fallback
│   └── config.py            # paths, constants, env vars
├── claude-integration/      # Claude Code wiring
│   ├── install.sh           # MCP registration + hooks + skills
│   ├── merge-settings.py    # hooks merger for settings.json
│   ├── settings.snippet.json # hook definitions
│   ├── claude.md.snippet    # CLAUDE.md instructions
│   ├── skills/              # /kb-search, /kb-capture, /kb-consolidate
│   └── hooks/               # SessionStart, Stop hooks
├── systemd/                 # systemd user units
│   ├── kb-watch.service     # file watcher service template
│   ├── kb-mcp-server.service # MCP HTTP daemon template
│   └── install.sh           # unit installer (resolves uv, substitutes @UV_BIN@)
├── bin/
│   ├── kb-health            # full stack health check
│   └── kb-server-wrapper.sh # (deprecated, see ADR-013)
├── docs/                    # project documentation
│   ├── constitution.md
│   ├── spec.md
│   ├── plan.md              # this file
│   ├── tasks.md
│   └── decisions/           # ADR-001 through ADR-017
├── vault/                   # vault repo (separate git, gitignored here)
│   ├── _meta/               # templates + schema (in structure repo)
│   └── ...                  # personal notes (in vault repo)
├── index/                   # generated indexes (gitignored)
│   ├── fts.sqlite
│   └── vectors.lance/
├── .logs/                   # service logs (gitignored)
├── bootstrap.sh             # fresh machine setup
└── pyproject.toml
```

---

## MCP Transport Modes

| Mode | Command | Use case |
|------|---------|----------|
| HTTP (primary) | `kb-server --transport http --port 3333` | Multi-session, multi-tool (registered as systemd unit) |
| stdio (fallback) | `kb-server` | Single session, no systemd (registered via `claude mcp add stdio`) |

Claude Code selects the mode based on the registered MCP config (`claude mcp list`).

---

## Key Design Decisions

See `docs/decisions/` for full ADRs. Summary of most impactful:

- **ADR-001**: Two-repo design separates vault from infrastructure.
- **ADR-004**: Hybrid FTS5 + LanceDB with RRF for best-of-both search.
- **ADR-011**: Lazy lancedb import reduces server startup from 3.4s → 1.2s.
- **ADR-013**: HTTP daemon eliminates per-session process overhead.
- **ADR-014**: MCP registration must go through `claude mcp add`, not settings.json.

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `KB_VAULT` | `~/kb/vault` | Vault root directory |
| `KB_MCP_PORT` | `3333` | HTTP server port |
| `KB_EMBED_DIM` | `768` | Embedding vector dimension |
| `PYENV_ROOT` | `~/.pyenv` | Used by systemd/install.sh to resolve uv |
