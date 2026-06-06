# kb — Tasks

Feature Branch: `main`  
Created: 2026-06-06  
Status: Active  
Spec: [docs/spec.md](spec.md) | Plan: [docs/plan.md](plan.md)

---

## Phase 1: Foundation (Complete)

- [x] Python package structure (`kb/`, `pyproject.toml`, `uv`)
- [x] FTS5 indexer with incremental mtime tracking (ADR-015)
- [x] LanceDB vector store with Ollama embeddings (ADR-009, ADR-010)
- [x] H2 + sliding window chunking (ADR-005)
- [x] Metadata-prefixed embeddings (ADR-006)
- [x] Hybrid RRF search (ADR-004)
- [x] FTS5 query syntax fallback (ADR-007)
- [x] Per-note RRF deduplication (ADR-008)
- [x] MCP server with 6 tools (stdio transport)
- [x] CLI tools (`kb-index`, `kb-search`, `kb-new`, `kb-watch`)
- [x] Two-repo vault structure (ADR-001)
- [x] YAML frontmatter schema with soft validation (ADR-003)
- [x] Wikilink backlink graph (ADR-016)
- [x] File-based note IDs (ADR-002)
- [x] Claude Code integration (skills, hooks, settings)
- [x] `bin/kb-health` health check script
- [x] `bootstrap.sh` for fresh machine setup
- [x] systemd user unit for kb-watch (ADR-017)

---

## Phase 2: HTTP Daemon + Documentation (Complete as of 2026-06-06)

- [x] Lazy import of lancedb/vector/embed (ADR-011) — startup 3.4s → 1.2s
- [x] Fix MCP registration: `claude mcp add --scope user` → `~/.claude.json` (ADR-014)
- [x] HTTP transport mode (`kb-server --transport http`) (ADR-013)
- [x] StreamableHTTPSessionManager with `/health` endpoint
- [x] systemd unit for kb-mcp-server (ADR-017)
- [x] systemd/install.sh: resolves real uv binary (bypasses pyenv shim)
- [x] claude-integration/install.sh: HTTP registration with stdio fallback
- [x] bin/kb-health: HTTP probe replaces stdio MCP handshake
- [x] Logs moved to `<KB_DIR>/.logs/` (gitignored)
- [x] 17 ADRs written to `docs/decisions/`
- [x] spec-kit docs: constitution, spec, plan, tasks

---

## Phase 3: Multi-Tool & Portability (Backlog)

### Multi-tool support
- [ ] Test Codex integration (configure `~/.codex/config.json` with HTTP URL)
- [ ] Test GitHub Copilot VS Code extension with `.vscode/mcp.json`
- [ ] Document per-tool configuration in README

### Cross-machine vault sync
- [ ] Validate vault repo pull/push workflow (conflicts, merge strategies for notes)
- [ ] Add `kb sync` CLI command wrapping `git -C vault pull && kb-index`)
- [ ] Document vault backup strategy

### Search quality
- [ ] Evaluate larger embedding models (e.g., `nomic-embed-text:v1.5`, `mxbai-embed-large`)
- [ ] Add reranking step (cross-encoder or LLM-based) for top-k results
- [ ] Tune `k_fts`, `k_vec`, `rrf_k` for larger vaults (>500 notes)

### Observability
- [ ] Add structured logging to kb-mcp-server (JSON logs for `kb-health` parsing)
- [ ] Track tool call metrics (latency, hit rate per tool)
- [ ] `kb-health` check: vault note count vs. index count (detect stale index)

### macOS / non-systemd support
- [ ] launchd plist equivalent for macOS (`~/Library/LaunchAgents/`)
- [ ] Docker compose for container use (stdio-only mode)

### Web UI (stretch)
- [ ] Read-only search UI (Starlette + HTMX over the same HTTP port)
- [ ] Vault browser with backlink graph visualization

---

## Dependency Map

```
Phase 3 multi-tool  →  depends on Phase 2 HTTP daemon ✓
Phase 3 cross-machine  →  depends on Phase 1 two-repo design ✓
Phase 3 search quality  →  depends on Phase 1 index pipeline ✓
Phase 3 macOS support  →  independent (new deployment path)
Phase 3 web UI  →  depends on HTTP daemon ✓
```
