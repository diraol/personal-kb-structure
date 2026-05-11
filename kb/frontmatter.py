"""Parse + validate vault note frontmatter."""
from __future__ import annotations
import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path

import frontmatter

from kb.config import VALID_TYPES

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


@dataclass
class Note:
    path: Path
    id: str
    type: str
    title: str
    project: str | None
    tags: list[str]
    aliases: list[str]
    sources: list[str]
    related: list[str]
    status: str
    created: str
    updated: str
    body: str
    wikilinks: list[str] = field(default_factory=list)

    @property
    def rel_path(self) -> str:
        from kb.config import VAULT_DIR
        try:
            return str(self.path.relative_to(VAULT_DIR))
        except ValueError:
            return str(self.path)


class FrontmatterError(ValueError):
    pass


def _coerce_list(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        return [v]
    return [str(x) for x in v]


def _coerce_date(v, field_name: str, path: Path) -> str:
    if isinstance(v, dt.date):
        return v.isoformat()
    if isinstance(v, str):
        return v
    raise FrontmatterError(f"{path}: {field_name} must be a date or ISO string, got {type(v).__name__}")


def parse_note(path: Path) -> Note:
    raw = path.read_text(encoding="utf-8")
    try:
        post = frontmatter.loads(raw)
    except Exception as e:
        raise FrontmatterError(f"{path}: cannot parse frontmatter: {e}") from e

    meta = post.metadata
    body = post.content

    if not meta:
        raise FrontmatterError(f"{path}: missing frontmatter block")

    note_type = meta.get("type")
    if note_type not in VALID_TYPES:
        raise FrontmatterError(f"{path}: invalid type {note_type!r}, must be one of {sorted(VALID_TYPES)}")

    note_id = meta.get("id") or path.stem
    title = meta.get("title")
    if not title:
        m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        title = m.group(1).strip() if m else note_id

    created = _coerce_date(meta.get("created", dt.date.today()), "created", path)
    updated = _coerce_date(meta.get("updated", created), "updated", path)

    wikilinks = sorted(set(WIKILINK_RE.findall(body)))

    return Note(
        path=path,
        id=note_id,
        type=note_type,
        title=title,
        project=meta.get("project"),
        tags=_coerce_list(meta.get("tags")),
        aliases=_coerce_list(meta.get("aliases")),
        sources=_coerce_list(meta.get("sources")),
        related=_coerce_list(meta.get("related")),
        status=meta.get("status", "active"),
        created=created,
        updated=updated,
        body=body,
        wikilinks=wikilinks,
    )


def iter_notes(vault_dir: Path):
    for p in sorted(vault_dir.rglob("*.md")):
        try:
            yield parse_note(p)
        except FrontmatterError as e:
            print(f"[skip] {e}")
