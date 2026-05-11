---
name: kb-consolidate
description: |
  At the end of a substantive session, distill the conversation into permanent vault
  notes — capturing decisions made, gotchas encountered, new domain understanding,
  and references discovered. Use when the user says "wrap up", "consolidate",
  "save what we learned", "end of session", "before I close this", or proactively
  at the natural close of a meaningful work session.
tags:
  - knowledge-base
  - consolidation
  - mcp
category: knowledge
---

# kb-consolidate

Sweep the current conversation for material worth persisting and write it to the vault.

## When to run

- User explicitly asks ("wrap up", "save learnings", "consolidate session").
- A long session is ending and substantive work happened (multiple edits, decisions,
  debugging).
- The user reveals a non-obvious pattern, a corrected approach, or a useful resource.

## Process

1. **Scan the conversation** for these signals:
   - **Decisions** — "let's go with X because Y", "we decided", trade-off discussions.
   - **Gotchas** — bugs found, surprising behaviors, "the issue was actually...".
   - **Domain learning** — new mental models, library quirks, architecture insights.
   - **References** — Confluence/Jira/Slack/dashboard URLs the user shared.
   - **User feedback** — corrections, preferences, "don't do X", "always do Y".

2. **Cluster by type** and propose a short list:
   ```
   Proposed captures:
   1. decision · "Use LanceDB for vector store" (project: kb)
   2. gotcha   · "Ollama embed dim 768 differs from default 1024" (project: kb)
   3. memory   · "User prefers files-first over server-first architecture"
   ```
   Ask the user to confirm / drop / merge before writing.

3. **For each confirmed item**, draft title + body following the type's template,
   then call `kb_capture`. Cite source — the conversation thread or the file that
   triggered the realization.

4. **Update existing notes** when the learning extends a previous note rather than
   replacing it (use `kb_search` → `kb_get` → edit the file directly).

5. **Report** — list the paths written or updated.

## Avoid

- Don't capture the play-by-play of the session. Capture the *learning*, not the *log*.
- Don't auto-write without user confirmation when the proposed list has > 1 item —
  the user is the editor of their own knowledge base.
- Don't capture material already in code, CLAUDE.md, or existing vault notes.
