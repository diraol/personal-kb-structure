# ADR-004: Hybrid Search via FTS5 + LanceDB Combined with Reciprocal Rank Fusion

**Status:** Accepted  
**Date:** 2026-05-11

## Context

Keyword search (FTS) excels at exact term matches but misses semantic synonyms. Vector search excels at semantic similarity but misses keyword precision. Either alone leaves gaps.

## Decision

Run both FTS5 (SQLite full-text search) and LanceDB (vector similarity) independently, then merge results using **Reciprocal Rank Fusion (RRF)**:

```
score(doc, rank) = 1 / (k + rank + 1)   where k = 60
```

Each source retrieves up to 30 candidates. Scores are summed per note (not per chunk — see ADR-008). Results are sorted by combined score descending. If vector search is unavailable (Ollama down), FTS results are returned alone with a `_warning` field.

## Consequences

- **+** Better recall than either method alone, especially for paraphrased queries.
- **+** Graceful degradation when embeddings are unavailable.
- **+** RRF is parameter-free in practice (`k=60` is well-established).
- **−** Two index lookups per query (slight latency vs. single-source).
- **−** Tuning `k_fts`, `k_vec`, `rrf_k` requires experimentation for different vault sizes.
