# ADR-005: Chunk-Level Indexing with H2 Headings + Sliding Window Overflow

**Status:** Accepted  
**Date:** 2026-05-11

## Context

Long notes span multiple topics. Embedding or indexing an entire note produces a single vector that averages all topics, reducing retrieval precision. The alternative is to split notes into chunks before indexing.

## Decision

Split notes into chunks using a two-pass strategy:

1. **H2 boundary split**: Split on `## Heading` markers. Each section becomes a chunk with its heading as `section` metadata.
2. **Sliding window overflow**: If a section exceeds `CHUNK_MAX_CHARS` (default 1500), split it further into overlapping windows of `CHUNK_OVERLAP_CHARS` (default 200) to prevent phrase boundaries being cut.

The preamble before the first H2 is treated as a chunk with `section=None`. Each chunk carries `(note_id, chunk_seq, section, text)`. Both FTS5 and LanceDB index at chunk level.

## Consequences

- **+** Section-level retrieval precision — a search for topic X in a multi-topic note returns the right section.
- **+** Overlap prevents important phrases spanning chunk boundaries.
- **−** A note can appear multiple times in raw results (deduped at RRF stage — see ADR-008).
- **−** Index size grows proportionally to chunk count, not note count.
