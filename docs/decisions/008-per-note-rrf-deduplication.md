# ADR-008: Per-Note Deduplication in RRF (Not Per-Chunk)

**Status:** Accepted  
**Date:** 2026-05-11

## Context

Since indexing is chunk-level (ADR-005), both FTS5 and LanceDB can return multiple chunks from the same note. The MCP tool result should be note-level (one entry per note with the best matching chunk), not chunk-level (many entries from the same note).

## Decision

After computing RRF scores per `(note_id, chunk_seq)` key, deduplicate to one entry per `note_id` by keeping the chunk with the highest RRF score. The final result set contains at most one entry per note, carrying the section and snippet of the best-matching chunk.

## Consequences

- **+** Tool output is clean and scannable — one result per note, not one per section.
- **+** `limit=10` returns 10 distinct notes, not 10 chunks from possibly 2-3 notes.
- **−** If a note is highly relevant in two sections, only one section is surfaced. The user must call `kb_get` to see the full note.
- **−** Notes with many highly-ranked chunks may still dominate results at the expense of other notes.
