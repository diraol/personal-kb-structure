# kb — local LLM-friendly knowledge base

Markdown vault + hybrid (keyword + semantic) retrieval, exposed to Claude Code via an MCP server. Notes are the source of truth; indexes are rebuildable.

## Two-repo design

This repo (**structure**) contains the infrastructure and is machine-agnostic.
Vault notes live in a **separate repo** cloned into `vault/`:

| Repo | Contains | Tracked by git |
|------|----------|----------------|
| `personal-kb-structure` (this repo) | Python package, MCP server, CLI, claude-integration, systemd, `vault/_meta/` templates | yes |
| Per-machine vault repo (e.g. `diraol-personal-kb`) | `vault/projects/`, `vault/domains/`, `vault/memory/`, `vault/references/` | yes — in its own nested `.git/` |

`vault/` on disk is a nested git repo. The structure repo gitignores note dirs;
`vault/.gitignore` ignores `_meta/` (owned by the structure repo).
Each machine or context uses its own vault remote — the structure repo stays shared.

## Layout

```
vault/                  split across two repos (see above)
  _meta/                ← structure repo: templates, tags, frontmatter spec
  projects/<name>/      ← vault repo: per-project notes
  domains/              ← vault repo: cross-project concepts
  references/           ← vault repo: pointers to external systems
  memory/               ← vault repo: session-accumulated learnings

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
git clone git@github.com:diraol/personal-kb-structure.git ~/kb
cd ~/kb

# With your vault repo (recommended):
./bootstrap.sh --vault-repo git@github.com:YOUR-ORG/YOUR-vault-repo.git

# Without a vault (empty, local-only notes):
./bootstrap.sh
```

Skipping pieces:
```bash
./bootstrap.sh --vault-repo <url> --no-watcher        # don't enable systemd unit
./bootstrap.sh --vault-repo <url> --no-embeddings     # FTS-only (no Ollama needed)
```

Day-to-day vault git operations:
```bash
git -C ~/kb/vault pull                          # pull latest notes
git -C ~/kb/vault add . && git -C ~/kb/vault commit -m "notes: ..." && git -C ~/kb/vault push
```

Then **restart Claude Code** so the `kb` MCP server and hooks load.

## Day-to-day

```bash
uv run kb-search "datomic cas"     # CLI hybrid search
uv run kb-new decision foo --project kb
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
