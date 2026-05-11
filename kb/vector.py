"""LanceDB vector store for semantic search over note chunks."""
from __future__ import annotations
from pathlib import Path

import lancedb
import pyarrow as pa

from kb.config import VECTORS_DB, EMBED_DIM


CHUNKS_TABLE = "chunks"


def _schema() -> pa.Schema:
    return pa.schema([
        pa.field("note_id", pa.string()),
        pa.field("path", pa.string()),
        pa.field("type", pa.string()),
        pa.field("project", pa.string()),
        pa.field("title", pa.string()),
        pa.field("section", pa.string()),
        pa.field("chunk_seq", pa.int32()),
        pa.field("text", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), EMBED_DIM)),
    ])


def connect(db_path: Path | None = None):
    p = db_path or VECTORS_DB
    p.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(p))
    if CHUNKS_TABLE not in db.table_names():
        db.create_table(CHUNKS_TABLE, schema=_schema())
    return db


def table(db=None):
    db = db or connect()
    return db.open_table(CHUNKS_TABLE)


def delete_note(db, note_id: str) -> None:
    tbl = table(db)
    tbl.delete(f"note_id = '{_escape(note_id)}'")


def upsert_chunks(db, rows: list[dict]) -> None:
    if not rows:
        return
    tbl = table(db)
    note_ids = {r["note_id"] for r in rows}
    for nid in note_ids:
        tbl.delete(f"note_id = '{_escape(nid)}'")
    tbl.add(rows)


def search(
    db,
    vector: list[float],
    *,
    limit: int = 20,
    note_type: str | None = None,
    project: str | None = None,
) -> list[dict]:
    q = table(db).search(vector).limit(limit)
    clauses = []
    if note_type:
        clauses.append(f"type = '{_escape(note_type)}'")
    if project:
        clauses.append(f"project = '{_escape(project)}'")
    if clauses:
        q = q.where(" AND ".join(clauses))
    return [
        {**r, "score": r.get("_distance", 0.0)}
        for r in q.to_list()
    ]


def _escape(s: str) -> str:
    return s.replace("'", "''")
