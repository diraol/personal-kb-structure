# ADR-016: Wikilink-Driven Backlink Graph in FTS DB

**Status:** Accepted  
**Date:** 2026-05-11

## Context

Notes reference each other via `[[note-id]]` and `[[note-id|display text]]` syntax. Exposing backlinks (which notes link to a given note) is useful for discovering related context. This requires a graph structure.

## Decision

During indexing, extract all wikilinks from each note body via regex and store them as edges in a `wikilinks` table in the FTS SQLite database: `(source_id, target_id)`. The `kb_related` MCP tool queries this table to return backlinks for a given note ID.

Only the target note ID is stored (display text is stripped). The regex handles both `[[id]]` and `[[id|display]]` forms.

## Consequences

- **+** `kb_related` provides graph traversal without a separate graph database.
- **+** Wikilinks are a natural part of the markdown authoring workflow.
- **−** Wikilinks to non-existent notes are stored silently — no broken link detection.
- **−** Link extraction is regex-based; edge cases (links in code blocks, escaped brackets) may produce false positives.
