# ADR-006: Metadata-Prefixed Embeddings

**Status:** Accepted  
**Date:** 2026-05-11

## Context

Embedding only the chunk text ignores structured metadata (title, section, tags) that is highly relevant to semantic meaning. Including metadata shifts the embedding vector toward the note's declared topic, not just its body text.

## Decision

Each chunk is embedded as a composed string:

```
{title} / {section} [{tag1}, {tag2}]\n\n{chunk_text}
```

If `section` is None (preamble), it is omitted. Tags are formatted as a bracketed list. This prefix is prepended to the chunk text before calling Ollama.

## Consequences

- **+** Title and tags bias the embedding toward the intended topic, improving recall for topic-level queries.
- **+** Section headings help disambiguate which part of a multi-topic note is most relevant.
- **−** The metadata prefix consumes embedding token budget, slightly reducing the effective chunk text window.
- **−** If the title/tags are inaccurate, they can pull the embedding away from the actual content.
