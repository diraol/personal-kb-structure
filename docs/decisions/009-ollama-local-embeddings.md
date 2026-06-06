# ADR-009: Ollama for Local Embeddings

**Status:** Accepted  
**Date:** 2026-05-11

## Context

Semantic search requires an embedding model. Options include cloud APIs (OpenAI, Cohere), local models via `sentence-transformers`, or Ollama. The vault contains personal and potentially sensitive knowledge.

## Decision

Use **Ollama** with the `nomic-embed-text` model (768 dimensions) for all embeddings. Ollama runs fully locally; no data leaves the machine. The model is pulled on first bootstrap. The client is a singleton (`kb/embed.py:_client`) cached for the process lifetime.

## Consequences

- **+** Complete privacy — vault contents never sent to external APIs.
- **+** Works offline after the model is pulled.
- **+** Ollama manages model downloads and GPU/CPU dispatch automatically.
- **−** Requires Ollama to be installed and running (`ollama serve`). If the daemon is down, semantic search silently degrades to FTS-only.
- **−** `nomic-embed-text` (768-dim) is a reasonable but not state-of-the-art model. Swapping models requires reindexing.
- **−** First startup after `ollama pull` is slow; subsequent calls are fast.
