"""Thin helpers re-used by CLI and MCP server. Keeps imports flat."""
from __future__ import annotations
from kb import fts as fts_mod


def _safe_fts(con, query, limit, note_type, project, tag):
    """FTS5 raises on syntax errors (e.g. unquoted special chars). Fall back to phrase."""
    try:
        return fts_mod.search(con, query, limit=limit, note_type=note_type, project=project, tag=tag)
    except Exception:
        safe = '"' + query.replace('"', '""') + '"'
        try:
            return fts_mod.search(con, safe, limit=limit, note_type=note_type, project=project, tag=tag)
        except Exception:
            return []
