# ADR-007: FTS5 Query Syntax Fallback

**Status:** Accepted  
**Date:** 2026-05-11

## Context

FTS5 has a query syntax (operators like `AND`, `OR`, `NOT`, `"quoted phrases"`, prefix `*`). Users passing natural language queries can inadvertently produce invalid FTS5 syntax (e.g., unmatched quotes, trailing operators), causing SQLite to raise an exception.

## Decision

Wrap the FTS5 query in a try/except. On `sqlite3.OperationalError`, retry with the original query wrapped in double quotes, converting it to a phrase search. This is implemented in `kb/search_helpers.py:_safe_fts()`.

## Consequences

- **+** Natural language queries never surface a raw SQLite error to the user.
- **+** Phrase search is a reasonable fallback for most user queries.
- **−** Silently downgrades from keyword search to phrase search; user sees degraded results without explanation (the `_warning` field is not set for this fallback).
- **−** A quoted phrase that is itself malformed still fails (e.g., a string with an embedded quote character).
