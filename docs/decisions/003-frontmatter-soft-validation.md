# ADR-003: Frontmatter Schema with Soft Validation

**Status:** Accepted  
**Date:** 2026-05-11

## Context

Notes must carry structured metadata (`type`, `created`, `updated`, `tags`, etc.) for filtering and display. The indexer needs to decide what to do with malformed notes.

## Decision

Parse frontmatter with `python-frontmatter`. Validate that `type` is one of the known enum values and that date fields are valid ISO dates or `datetime.date` objects. On validation failure, print a warning and **skip** the note — the indexer continues rather than failing.

If `title` is missing from frontmatter, derive it from the first H1 heading in the note body.

## Consequences

- **+** A single malformed note doesn't block indexing of the entire vault.
- **+** Allows iterative adoption — old notes without strict schema still partially work.
- **−** Silently skipped notes are invisible until the user runs `kb-health` or notices missing search results.
- **−** No enforcement at write time; invalid notes can accumulate.
