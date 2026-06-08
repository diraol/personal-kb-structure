#!/usr/bin/env python3
"""Shared KB session context hook logic for Claude and Codex."""
import argparse
import json
import os
from pathlib import Path
import sys

MAX_BYTES = int(os.environ.get("AGENT_KB_CONTEXT_MAX_BYTES", os.environ.get("CODEX_KB_CONTEXT_MAX_BYTES", "24000")))


def read_payload():
    try:
        data = sys.stdin.read()
        if data.strip():
            return json.loads(data)
    except Exception:
        pass
    return {}


def payload_cwd(payload):
    candidates = [
        payload.get("cwd"),
        payload.get("workdir"),
        payload.get("working_dir"),
        payload.get("current_working_directory"),
        os.environ.get("CLAUDE_PROJECT_DIR"),
        os.environ.get("CODEX_CWD"),
    ]
    session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
    candidates.extend([session.get("cwd"), session.get("workdir"), session.get("working_dir")])
    for value in candidates:
        if isinstance(value, str) and value:
            return Path(value).expanduser()
    return Path.cwd()


def find_project_slug(cwd):
    cur = cwd.resolve()
    home = Path.home().resolve()
    for path in [cur, *cur.parents]:
        marker = path / ".kb-project"
        if marker.is_file():
            lines = marker.read_text(errors="replace").splitlines()
            if lines:
                slug = lines[0].strip()
                if slug:
                    return slug
        if path == home:
            break
    return cur.name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", choices=["claude", "codex"], required=True)
    parser.parse_args()

    payload = read_payload()
    vault = Path(os.environ.get("KB_VAULT", str(Path.home() / "kb" / "vault"))).expanduser()
    projects = vault / "projects"
    if not projects.is_dir():
        return 0

    cwd = payload_cwd(payload)
    slug = find_project_slug(cwd)
    idx = projects / slug / "_index.md"
    if not idx.is_file():
        return 0

    content = idx.read_bytes()[:MAX_BYTES]
    truncated = idx.stat().st_size > len(content)
    text = content.decode("utf-8", errors="replace")

    print(f'<kb-project-context project="{slug}" source="{idx}">')
    print(text.rstrip())
    if truncated:
        print(f"\n[truncated to {MAX_BYTES} bytes]")
    print("</kb-project-context>\n")
    print("Tip: use the kb MCP tools, especially kb_search, kb_get, kb_related, and kb_capture, for deeper retrieval and persistence.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
