# knowldege — local LLM-friendly knowledge base

Markdown vault + hybrid (keyword + semantic) retrieval, exposed to Claude Code via an MCP server. Notes are the source of truth; indexes are rebuildable.

## Layout

```
vault/                  source of truth, markdown with YAML frontmatter
  projects/<name>/      per-project: _index.md, architecture/, decisions/, gotchas/, sessions/
  domains/              cross-project: clojure/, diplomat/, nubank-platform/, ...
  references/           pointers: confluence/, jira/, slack/, dashboards/
  memory/               session-accumulated: facts/, decisions/, corrections/
  _meta/templates/      note templates

index/                  generated, gitignored
  fts.sqlite            SQLite FTS5 (keyword)
  vectors.lance/        LanceDB (semantic via Ollama nomic-embed-text)

kb/                     Python package (indexer, MCP server, embeddings)
bin/                    CLI entrypoints (kb-index, kb-search, kb-watch, kb-new)
```

## Note conventions

Every `.md` file under `vault/` has YAML frontmatter — see [`vault/_meta/frontmatter.md`](vault/_meta/frontmatter.md). Wikilinks (`[[note-name]]`) build the backlink graph.

## Quickstart

```bash
uv sync                            # install Python deps
ollama pull nomic-embed-text       # one-time
uv run kb-index                    # build/refresh indexes
uv run kb-search "datomic cas"     # CLI hybrid search

# Background watcher (incremental reindex on save)
systemctl --user enable --now kb-watch
```

## Claude Code integration

- **MCP server** `kb` exposes `kb_search`, `kb_get`, `kb_recent`, `kb_related`, `kb_capture`, `kb_list_projects`.
- **Skills** `kb-search`, `kb-capture`, `kb-consolidate` (in `~/.claude/skills/`).
- **Hooks** SessionStart injects current project's `_index.md`; Stop prompts consolidation after substantive sessions.

## Adding notes

```bash
uv run kb-new project <name>       # scaffold project folder
uv run kb-new decision <slug>      # ADR-style entry
uv run kb-new gotcha <slug>
```

Or just drop a markdown file anywhere under `vault/` with valid frontmatter — the watcher picks it up.
