"""Split a note body into embedding-friendly chunks.

Strategy: split on H2 headings. If a chunk is still too long, fall back to
char-window split with overlap.
"""
from __future__ import annotations
import re
from dataclasses import dataclass

from kb.config import CHUNK_MAX_CHARS, CHUNK_OVERLAP_CHARS

H2_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


@dataclass
class Chunk:
    section: str | None
    seq: int
    text: str


def chunk_body(body: str) -> list[Chunk]:
    body = body.strip()
    if not body:
        return []

    sections: list[tuple[str | None, str]] = []
    headings = [(m.start(), m.group(1).strip()) for m in H2_RE.finditer(body)]
    if not headings:
        sections.append((None, body))
    else:
        first_start = headings[0][0]
        if first_start > 0:
            preamble = body[:first_start].strip()
            if preamble:
                sections.append((None, preamble))
        for i, (start, name) in enumerate(headings):
            end = headings[i + 1][0] if i + 1 < len(headings) else len(body)
            sections.append((name, body[start:end].strip()))

    chunks: list[Chunk] = []
    seq = 0
    for section, text in sections:
        for piece in _window_split(text, CHUNK_MAX_CHARS, CHUNK_OVERLAP_CHARS):
            chunks.append(Chunk(section=section, seq=seq, text=piece))
            seq += 1
    return chunks


def _window_split(text: str, max_chars: int, overlap: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    out, start = [], 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        out.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return out
