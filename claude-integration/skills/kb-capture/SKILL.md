---
name: kb-capture
description: |
  Append a new note to the local kb vault (memory, decision, gotcha, or
  reference). Use when the user shares something worth carrying into future sessions:
  a decision was made, a non-obvious behavior was discovered, a useful external
  resource was identified, or a fact about how the user works/thinks is revealed.
  Triggers on: "save this", "remember this", "note that", "capture this",
  "we decided", "the gotcha is", "for future reference", "add to vault",
  "kb capture", "record this decision".
tags:
  - knowledge-base
  - capture
  - mcp
category: knowledge
---

# kb-capture

Persist knowledge to the vault via `kb_capture`. The MCP tool writes a frontmatter
note in the correct folder, then incrementally reindexes it.

## When to capture

- **decision** — A choice was made between alternatives. Includes: context, decision,
  alternatives considered, consequences. Always project-scoped.
- **gotcha** — Non-obvious behavior bit us. Includes: symptom, root cause, fix, how to
  spot it next time. Always project-scoped.
- **memory** — A fact about preferences, conventions, or learnings worth carrying
  forward (often cross-project). Lead with the rule. Add **Why** and **How to apply**.
- **reference** — A pointer to an external resource (Confluence page, Slack channel,
  dashboard, doc). Light note — describe the resource and when to consult it.

## How to use

1. **Confirm the type.** If ambiguous, ask the user before writing.
2. **Draft a title.** Short, specific, searchable. Title becomes the H1.
3. **Compose the body.** Follow the template structure for the chosen type (see
   `vault/_meta/templates/`). Don't pad.
4. **Tag liberally** but prefer existing tags (`vault/_meta/tags.md`).
5. **Link** to related notes with wikilinks `[[other-note-id]]` in the body.
6. **Call `kb_capture`** with `type`, `title`, `body`, optional `project`, `tags`,
   `sources`, `related`.

## Don't

- Don't duplicate. Run `kb_search` first to see if a note already covers this — update
  it instead (read it, edit the file, save).
- Don't capture ephemeral state (current task progress, in-flight conversation
  context). Those belong in plans/tasks, not memory.
- Don't capture content already documented in code or CLAUDE.md.
- Don't capture sensitive credentials, tokens, or PII.

## After capture

Mention the path to the new note so the user can edit it if needed.
