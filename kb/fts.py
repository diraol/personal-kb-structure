"""SQLite FTS5 keyword index over notes and chunks."""
from __future__ import annotations
import sqlite3
from pathlib import Path

from kb.config import FTS_DB
from kb.frontmatter import Note
from kb.chunk import Chunk

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    project TEXT,
    tags TEXT,
    aliases TEXT,
    sources TEXT,
    related TEXT,
    status TEXT,
    created TEXT,
    updated TEXT,
    mtime REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notes_type ON notes(type);
CREATE INDEX IF NOT EXISTS idx_notes_project ON notes(project);
CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated);

CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    note_id UNINDEXED,
    chunk_seq UNINDEXED,
    section,
    body,
    title,
    tags,
    tokenize = 'unicode61 remove_diacritics 2'
);

CREATE TABLE IF NOT EXISTS wikilinks (
    src TEXT NOT NULL,
    dst TEXT NOT NULL,
    PRIMARY KEY (src, dst)
);
CREATE INDEX IF NOT EXISTS idx_wl_dst ON wikilinks(dst);
"""


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    p = db_path or FTS_DB
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def upsert_note(con: sqlite3.Connection, note: Note, chunks: list[Chunk], mtime: float) -> None:
    con.execute(
        """
        INSERT INTO notes(id, path, type, title, project, tags, aliases, sources, related, status, created, updated, mtime)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            path=excluded.path, type=excluded.type, title=excluded.title, project=excluded.project,
            tags=excluded.tags, aliases=excluded.aliases, sources=excluded.sources, related=excluded.related,
            status=excluded.status, created=excluded.created, updated=excluded.updated, mtime=excluded.mtime
        """,
        (
            note.id, note.rel_path, note.type, note.title, note.project,
            ",".join(note.tags), ",".join(note.aliases), ",".join(note.sources), ",".join(note.related),
            note.status, note.created, note.updated, mtime,
        ),
    )
    con.execute("DELETE FROM notes_fts WHERE note_id = ?", (note.id,))
    for ch in chunks:
        con.execute(
            "INSERT INTO notes_fts(note_id, chunk_seq, section, body, title, tags) VALUES(?,?,?,?,?,?)",
            (note.id, ch.seq, ch.section or "", ch.text, note.title, " ".join(note.tags)),
        )
    con.execute("DELETE FROM wikilinks WHERE src = ?", (note.id,))
    for dst in note.wikilinks:
        con.execute("INSERT OR IGNORE INTO wikilinks(src, dst) VALUES(?, ?)", (note.id, dst))


def delete_note_by_path(con: sqlite3.Connection, rel_path: str) -> None:
    row = con.execute("SELECT id FROM notes WHERE path = ?", (rel_path,)).fetchone()
    if not row:
        return
    note_id = row["id"]
    con.execute("DELETE FROM notes_fts WHERE note_id = ?", (note_id,))
    con.execute("DELETE FROM wikilinks WHERE src = ?", (note_id,))
    con.execute("DELETE FROM notes WHERE id = ?", (note_id,))


def search(
    con: sqlite3.Connection,
    query: str,
    *,
    limit: int = 20,
    note_type: str | None = None,
    project: str | None = None,
    tag: str | None = None,
) -> list[dict]:
    sql = """
        SELECT n.id, n.path, n.title, n.type, n.project, n.tags, n.updated,
               f.section, f.chunk_seq, snippet(notes_fts, 3, '[', ']', '…', 12) AS snippet,
               bm25(notes_fts) AS score
        FROM notes_fts f
        JOIN notes n ON n.id = f.note_id
        WHERE notes_fts MATCH ?
    """
    params: list = [query]
    if note_type:
        sql += " AND n.type = ?"
        params.append(note_type)
    if project:
        sql += " AND n.project = ?"
        params.append(project)
    if tag:
        sql += " AND (',' || n.tags || ',') LIKE ?"
        params.append(f"%,{tag},%")
    sql += " ORDER BY score LIMIT ?"
    params.append(limit)
    return [dict(r) for r in con.execute(sql, params).fetchall()]


def get_note(con: sqlite3.Connection, note_id: str) -> dict | None:
    row = con.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    return dict(row) if row else None


def recent(con: sqlite3.Connection, limit: int = 20, project: str | None = None) -> list[dict]:
    sql = "SELECT id, path, title, type, project, updated FROM notes"
    params: list = []
    if project:
        sql += " WHERE project = ?"
        params.append(project)
    sql += " ORDER BY updated DESC, mtime DESC LIMIT ?"
    params.append(limit)
    return [dict(r) for r in con.execute(sql, params).fetchall()]


def backlinks(con: sqlite3.Connection, note_id: str) -> list[dict]:
    rows = con.execute(
        """
        SELECT n.id, n.path, n.title, n.type, n.project
        FROM wikilinks w JOIN notes n ON n.id = w.src
        WHERE w.dst = ?
        """,
        (note_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def list_projects(con: sqlite3.Connection) -> list[dict]:
    rows = con.execute(
        """
        SELECT project AS name, COUNT(*) AS notes
        FROM notes WHERE project IS NOT NULL AND project != ''
        GROUP BY project ORDER BY notes DESC, project
        """
    ).fetchall()
    return [dict(r) for r in rows]
