"""Walk the vault, populate FTS5 + LanceDB. Incremental via mtime."""
from __future__ import annotations
from pathlib import Path
from typing import Iterable

from kb import fts, vector, embed
from kb.chunk import chunk_body
from kb.config import VAULT_DIR
from kb.frontmatter import Note, parse_note, FrontmatterError


def _file_mtime(p: Path) -> float:
    return p.stat().st_mtime


EXCLUDED_PARTS = {"templates"}


def _all_md(vault_dir: Path) -> Iterable[Path]:
    for p in vault_dir.rglob("*.md"):
        if EXCLUDED_PARTS.intersection(p.relative_to(vault_dir).parts):
            continue
        yield p


def _changed_paths(con, vault_dir: Path) -> tuple[list[Path], list[str]]:
    """Return (to_index, to_delete_rel_paths)."""
    on_disk = {p: _file_mtime(p) for p in _all_md(vault_dir)}
    on_disk_rel = {str(p.relative_to(vault_dir)): m for p, m in on_disk.items()}

    rows = con.execute("SELECT path, mtime FROM notes").fetchall()
    in_db = {r["path"]: r["mtime"] for r in rows}

    to_index = [
        p for p, m in on_disk.items()
        if str(p.relative_to(vault_dir)) not in in_db
        or in_db[str(p.relative_to(vault_dir))] < m
    ]
    to_delete = [rel for rel in in_db if rel not in on_disk_rel]
    return to_index, to_delete


def index_one(con, vdb, note: Note, *, with_embeddings: bool = True) -> int:
    chunks = chunk_body(note.body)
    fts.upsert_note(con, note, chunks, _file_mtime(note.path))
    if not with_embeddings or not chunks:
        return len(chunks)
    texts = [_compose_for_embedding(note, ch.section, ch.text) for ch in chunks]
    vecs = embed.embed(texts)
    rows = [
        {
            "note_id": note.id,
            "path": note.rel_path,
            "type": note.type,
            "project": note.project or "",
            "title": note.title,
            "section": ch.section or "",
            "chunk_seq": ch.seq,
            "text": ch.text,
            "vector": vec,
        }
        for ch, vec in zip(chunks, vecs)
    ]
    vector.upsert_chunks(vdb, rows)
    return len(chunks)


def _compose_for_embedding(note: Note, section: str | None, text: str) -> str:
    head = f"{note.title}"
    if section:
        head += f" / {section}"
    if note.tags:
        head += f" [{', '.join(note.tags)}]"
    return f"{head}\n\n{text}"


def reindex(*, paths: list[Path] | None = None, full: bool = False, with_embeddings: bool = True) -> dict:
    con = fts.connect()
    vdb = vector.connect() if with_embeddings else None
    stats = {"indexed": 0, "deleted": 0, "skipped": 0, "chunks": 0}

    if full:
        con.execute("DELETE FROM notes")
        con.execute("DELETE FROM notes_fts")
        con.execute("DELETE FROM wikilinks")
        if vdb is not None:
            try:
                vdb.drop_table(vector.CHUNKS_TABLE)
            except Exception:
                pass
            vdb = vector.connect()
        targets = list(_all_md(VAULT_DIR))
        to_delete: list[str] = []
    elif paths:
        targets = paths
        to_delete = []
    else:
        targets, to_delete = _changed_paths(con, VAULT_DIR)

    for rel in to_delete:
        fts.delete_note_by_path(con, rel)
        if vdb is not None:
            row = con.execute("SELECT id FROM notes WHERE path = ?", (rel,)).fetchone()
            if row:
                vector.delete_note(vdb, row["id"])
        stats["deleted"] += 1

    for p in targets:
        try:
            note = parse_note(p)
        except FrontmatterError as e:
            print(f"[skip] {e}")
            stats["skipped"] += 1
            continue
        n_chunks = index_one(con, vdb, note, with_embeddings=with_embeddings)
        stats["indexed"] += 1
        stats["chunks"] += n_chunks

    con.commit()
    con.close()
    return stats
