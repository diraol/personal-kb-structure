"""Hybrid search: FTS5 + LanceDB combined via reciprocal rank fusion."""
from __future__ import annotations
from collections import defaultdict

from kb import fts, vector, embed
from kb.search_helpers import _safe_fts


def hybrid_search(
    query: str,
    *,
    limit: int = 10,
    note_type: str | None = None,
    project: str | None = None,
    tag: str | None = None,
    k_fts: int = 30,
    k_vec: int = 30,
    rrf_k: int = 60,
) -> list[dict]:
    con = fts.connect()
    try:
        kw_results = _safe_fts(con, query, k_fts, note_type, project, tag)
    finally:
        con.close()

    vec_results: list[dict] = []
    try:
        vec = embed.embed([query])[0]
        vdb = vector.connect()
        vec_results = vector.search(vdb, vec, limit=k_vec, note_type=note_type, project=project)
    except Exception as e:
        vec_err = f"(semantic search unavailable: {type(e).__name__}: {e})"
    else:
        vec_err = None

    scores: dict[tuple[str, int], float] = defaultdict(float)
    enriched: dict[tuple[str, int], dict] = {}

    for rank, r in enumerate(kw_results):
        key = (r["id"], r.get("chunk_seq", 0))
        scores[key] += 1.0 / (rrf_k + rank + 1)
        enriched.setdefault(key, {**r, "_kw_rank": rank, "_vec_rank": None})

    for rank, r in enumerate(vec_results):
        key = (r["note_id"], r.get("chunk_seq", 0))
        scores[key] += 1.0 / (rrf_k + rank + 1)
        existing = enriched.get(key)
        if existing:
            existing["_vec_rank"] = rank
            existing.setdefault("text", r.get("text"))
            existing.setdefault("section", r.get("section"))
        else:
            enriched[key] = {
                "id": r["note_id"],
                "path": r.get("path"),
                "type": r.get("type"),
                "project": r.get("project"),
                "title": r.get("title"),
                "section": r.get("section"),
                "chunk_seq": r.get("chunk_seq"),
                "snippet": (r.get("text") or "")[:280],
                "_kw_rank": None,
                "_vec_rank": rank,
            }

    deduped: dict[str, dict] = {}
    for key, payload in enriched.items():
        nid = key[0]
        if nid not in deduped or scores[key] > scores[(nid, deduped[nid]["chunk_seq"] or 0)]:
            deduped[nid] = {**payload, "score": scores[key]}

    ranked = sorted(deduped.values(), key=lambda r: r["score"], reverse=True)
    if vec_err and not vec_results:
        for r in ranked:
            r["_warning"] = vec_err
    return ranked[:limit]
