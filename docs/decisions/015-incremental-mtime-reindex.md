# ADR-015: Incremental Reindex via mtime Tracking

**Status:** Accepted  
**Date:** 2026-05-11

## Context

Full reindexing of the entire vault on every save would be too slow for interactive use. The indexer needs to detect which notes have changed.

## Decision

The FTS5 database stores `mtime` (float, seconds since epoch) for each indexed note. On reindex, the indexer:
1. Scans all `.md` files in the vault for their current disk mtime.
2. Compares against stored mtimes; files where `disk_mtime > db_mtime` are queued for reindexing.
3. Files in the DB that no longer exist on disk are queued for deletion.

Deletion reindexes are called with `with_embeddings=False` — the FTS rows are removed and `vector.delete_note()` is called separately for LanceDB cleanup.

## Consequences

- **+** Only changed files are reindexed — fast enough for the file watcher's 800ms debounce.
- **+** Deletions are detected on the next watcher cycle, not just additions/modifications.
- **−** Vulnerable to clock skew (e.g., files copied from another machine with future mtimes).
- **−** Mtime granularity is 1 second on some filesystems; rapid edits within the same second may not trigger reindex.
