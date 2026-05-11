"""Paths and tunables. Override via env vars."""
from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(os.environ.get("KB_ROOT", Path(__file__).resolve().parent.parent))
VAULT_DIR = Path(os.environ.get("KB_VAULT", ROOT / "vault"))
INDEX_DIR = Path(os.environ.get("KB_INDEX", ROOT / "index"))
FTS_DB = INDEX_DIR / "fts.sqlite"
VECTORS_DB = INDEX_DIR / "vectors.lance"

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
EMBED_MODEL = os.environ.get("KB_EMBED_MODEL", "nomic-embed-text")
EMBED_DIM = int(os.environ.get("KB_EMBED_DIM", "768"))

CHUNK_MAX_CHARS = int(os.environ.get("KB_CHUNK_MAX_CHARS", "1500"))
CHUNK_OVERLAP_CHARS = int(os.environ.get("KB_CHUNK_OVERLAP_CHARS", "200"))

VALID_TYPES = {"project", "domain", "reference", "memory", "decision", "gotcha", "meta"}
