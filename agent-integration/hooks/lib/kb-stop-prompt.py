#!/usr/bin/env python3
"""Shared KB stop nudge hook logic for Claude and Codex."""
import argparse
import json
import os
from pathlib import Path
import sys


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
        os.environ.get("CLAUDE_PROJECT_DIR"),
        os.environ.get("CODEX_CWD"),
    ]
    session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
    candidates.extend([session.get("cwd"), session.get("workdir"), session.get("working_dir")])
    for value in candidates:
        if isinstance(value, str) and value:
            return Path(value).expanduser()
    return Path.cwd()


def has_kb_marker(cwd):
    cur = cwd.resolve()
    home = Path.home().resolve()
    for path in [cur, *cur.parents]:
        if (path / ".kb-project").is_file():
            return True
        if path == home:
            break
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", choices=["claude", "codex"], required=True)
    parser.parse_args()

    payload = read_payload()
    vault = Path(os.environ.get("KB_VAULT", str(Path.home() / "kb" / "vault"))).expanduser().resolve()
    cwd = payload_cwd(payload).resolve()
    kb_root = vault.parent

    if not (str(cwd).startswith(str(kb_root)) or has_kb_marker(cwd)):
        return 0

    print("[kb] If this session produced decisions, gotchas, or learnings worth keeping, use kb_capture or the KB MCP workflow before closing.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
