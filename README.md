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
claude-integration/     skills, hooks, settings snippet, install.sh
systemd/                kb-watch.service + install.sh
bootstrap.sh            fresh-machine end-to-end installer
```

## Note conventions

Every `.md` file under `vault/` has YAML frontmatter — see [`vault/_meta/frontmatter.md`](vault/_meta/frontmatter.md). Wikilinks (`[[note-name]]`) build the backlink graph.

## Bootstrap a fresh machine

```bash
git clone git@github.com:nubank/diraol-personal-kb.git ~/dev/knowldege
cd ~/dev/knowldege
./bootstrap.sh                     # uv sync + ollama check + index + claude wiring + watcher
```

Skipping pieces:
```bash
./bootstrap.sh --no-watcher        # don't enable systemd unit
./bootstrap.sh --no-embeddings     # FTS-only (no Ollama needed)
```

Then **restart Claude Code** so the `kb` MCP server and hooks load.

## Day-to-day

```bash
uv run kb-search "datomic cas"     # CLI hybrid search
uv run kb-new decision foo --project knowldege
uv run kb-index                    # incremental reindex (the watcher does this for you)
```

## Claude Code integration

Vendored in [`claude-integration/`](claude-integration/) — see its README for details.

- **MCP server** `kb` exposes `kb_search`, `kb_get`, `kb_recent`, `kb_related`, `kb_capture`, `kb_list_projects`.
- **Skills** `kb-search`, `kb-capture`, `kb-consolidate` (symlinked into `~/.claude/skills/`).
- **Hooks** SessionStart injects current project's `_index.md`; Stop nudges `/kb-consolidate` after vault sessions.

Re-apply the wiring after `git pull`:
```bash
./claude-integration/install.sh    # idempotent — safe to re-run
```

## Adding notes

```bash
uv run kb-new project <name>       # scaffold project folder
uv run kb-new decision <slug>      # ADR-style entry
uv run kb-new gotcha <slug>
```

Or just drop a markdown file anywhere under `vault/` with valid frontmatter — the watcher picks it up.
