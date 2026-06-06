# ADR-010: Fixed Embedding Dimension via KB_EMBED_DIM

**Status:** Accepted  
**Date:** 2026-05-11

## Context

LanceDB requires a fixed-dimension schema at table creation time. The embedding dimension must match the model in use. `nomic-embed-text` outputs 768 dimensions.

## Decision

The embedding dimension is configured via the `KB_EMBED_DIM` environment variable (default: 768). The LanceDB table schema is defined with this dimension at creation time. A mismatch between the configured dimension and the model's actual output is detected post-embedding (after the first batch) and raises a `ValueError`.

## Consequences

- **+** Dimension is explicit and configurable without code changes.
- **+** Schema is defined once at table creation; no runtime schema negotiation.
- **−** Switching models (e.g., to a 1536-dim model) requires: setting `KB_EMBED_DIM`, deleting `index/vectors.lance/`, and running `kb-index --full` to rebuild.
- **−** Dimension mismatch is caught late (after an embed call), not at startup.
