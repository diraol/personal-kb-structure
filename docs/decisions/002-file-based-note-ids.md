# ADR-002: File-Based Note IDs Derived from Title Slug

**Status:** Accepted  
**Date:** 2026-05-11

## Context

Notes need stable identifiers for wikilinks, backlinks, and MCP tool references (`kb_get`, `kb_related`). IDs could be explicit (user-defined), content-derived (hash), or path-derived.

## Decision

Note IDs default to `{type}-{kebab-case-title}` when captured via `kb_capture`, and to the filename stem when parsed from existing files. If frontmatter contains an explicit `id:` field, that takes precedence. The `_slugify()` function normalises to lowercase, strips non-alphanumeric characters, and collapses separators to `-`.

## Consequences

- **+** IDs are human-readable and predictable from the title.
- **+** No UUID generation; notes are portable as plain files.
- **+** Wikilinks `[[note-id]]` are stable as long as the title doesn't change.
- **−** Title changes silently break wikilinks (no rename tracking).
- **−** Two notes with the same slugified title collide; `kb_capture` returns an error rather than overwriting.
