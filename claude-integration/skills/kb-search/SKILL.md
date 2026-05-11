---
name: kb-search
description: |
  Retrieve contextualized knowledge from the local kb vault (markdown notes
  indexed with hybrid FTS5 + semantic search). Use this BEFORE asking the user for
  project context, conventions, past decisions, gotchas, or external reference info —
  the vault likely already has it. Triggers on: "what do we know about X",
  "any notes on", "past decisions", "have I documented", "look in the vault",
  "search my notes", "kb search", "what's the convention for", "have we seen this
  before", "is there a gotcha", "project context", "vault".
tags:
  - knowledge-base
  - retrieval
  - mcp
category: knowledge
---

# kb-search

Query the local kb vault via the `kb_*` MCP tools. The vault contains four
classes of notes:

- **project** — per-project context (architecture, decisions, gotchas, sessions)
- **domain** — cross-project concepts (Clojure, Diplomat, Datomic, Kafka, …)
- **reference** — pointers to external systems (Confluence, Jira, Slack, dashboards)
- **memory** — accumulated session learnings worth carrying forward

## When to use

- A user message references something project- or domain-specific and you lack context.
- The user explicitly asks to search/recall notes.
- Before recommending an approach, check if a relevant decision or gotcha already exists.
- At session start (optionally) to surface recent notes for the current project.

## How to use

1. **Start broad.** Call `kb_search` with the user's terms (no filters). Returns ranked
   chunks: title, path, type, project, section, snippet, score.
2. **Refine with filters.** Add `type` / `project` / `tag` if the broad search is noisy.
3. **Fetch full notes.** Call `kb_get(id=<note_id>)` for the top 1–3 hits to read the
   complete frontmatter + body. Snippets are not enough for nuanced topics.
4. **Walk the graph.** Use `kb_related(id=...)` to find backlinks — neighboring notes
   are often where the actual answer lives.
5. **Cite.** When using vault content in a response, reference the note path so the user
   can audit and edit. Format: `(see vault/projects/<x>/decisions/<y>.md)`.

## Filtering tips

- `type=decision` for ADR-style records.
- `type=gotcha` when a bug or surprising behavior is in play.
- `project=<slug>` to scope to a single project.
- `tag=incident` for post-incident learnings.

## Don't

- Don't paraphrase notes when an exact quote answers the question — quote and cite.
- Don't ignore stale `updated:` dates — flag if a note is older than 6 months and the
  topic is fast-moving.
- Don't search the vault for content that lives in code — read the file directly.

## After a useful retrieval

If the user reveals new context during the conversation that isn't yet captured, suggest
running `kb-capture` to persist it.
