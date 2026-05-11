"""Embeddings via Ollama (nomic-embed-text by default)."""
from __future__ import annotations
import ollama

from kb.config import OLLAMA_HOST, EMBED_MODEL, EMBED_DIM


_client: ollama.Client | None = None


def client() -> ollama.Client:
    global _client
    if _client is None:
        _client = ollama.Client(host=OLLAMA_HOST)
    return _client


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    resp = client().embed(model=EMBED_MODEL, input=texts)
    vecs = resp["embeddings"]
    if vecs and len(vecs[0]) != EMBED_DIM:
        raise RuntimeError(
            f"Embedding dim mismatch: model returned {len(vecs[0])}, config has KB_EMBED_DIM={EMBED_DIM}"
        )
    return vecs


def health() -> tuple[bool, str]:
    try:
        client().embed(model=EMBED_MODEL, input=["ping"])
        return True, "ok"
    except Exception as e:
        return False, str(e)
