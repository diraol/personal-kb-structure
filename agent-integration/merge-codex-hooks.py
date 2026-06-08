#!/usr/bin/env python3
"""Idempotently merge kb hook entries into ~/.codex/hooks.json.

- Substitutes ${CODEX_DIR} placeholder in the snippet.
- For hooks: appends each entry only if the same `command` isn't already wired.
- Always writes a timestamped backup of the original hooks.json.

Usage:
    python merge-codex-hooks.py [--repo <path>] [--hooks-json <path>] [--dry-run]
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path


def substitute(obj, env: dict[str, str]):
    if isinstance(obj, dict):
        return {k: substitute(v, env) for k, v in obj.items()}
    if isinstance(obj, list):
        return [substitute(x, env) for x in obj]
    if isinstance(obj, str):
        out = obj
        for k, v in env.items():
            out = out.replace("${" + k + "}", v)
        return out
    return obj


def merge_hooks(target_hooks: dict, new_hooks: dict) -> tuple[dict, list[str]]:
    """Append hook entries not already present (deduplicated by `command`)."""
    added = []
    for event, entries in new_hooks.items():
        existing_cmds: set[str] = set()
        for e in target_hooks.get(event, []):
            for h in e.get("hooks", []):
                if "command" in h:
                    existing_cmds.add(h["command"])
        bucket = target_hooks.setdefault(event, [])
        for e in entries:
            new_cmds = [h.get("command") for h in e.get("hooks", []) if "command" in h]
            if all(c in existing_cmds for c in new_cmds):
                continue
            bucket.append(e)
            added.extend(c for c in new_cmds if c not in existing_cmds)
    return target_hooks, added


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]),
                   help="Path to the kb repo.")
    p.add_argument("--hooks-json", default=str(Path.home() / ".codex" / "hooks.json"),
                   help="Target hooks.json path.")
    p.add_argument("--snippet", default=str(Path(__file__).with_name("hooks.snippet.json")),
                   help="Snippet template path.")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    codex_dir = str(Path.home() / ".codex")
    snippet_path = Path(args.snippet)
    hooks_path = Path(args.hooks_json)

    if not snippet_path.exists():
        sys.exit(f"snippet not found: {snippet_path}")

    env = {"CODEX_DIR": codex_dir, "HOME": str(Path.home())}
    snippet = json.loads(snippet_path.read_text())
    snippet = substitute(snippet, env)

    if hooks_path.exists():
        current = json.loads(hooks_path.read_text())
    else:
        current = {"hooks": {}}

    current.setdefault("hooks", {})
    merged_hooks, added_cmds = merge_hooks(current["hooks"], snippet.get("hooks", {}))
    current["hooks"] = merged_hooks

    if args.dry_run:
        print(json.dumps({"hooks_added": added_cmds}, indent=2))
        return 0

    if hooks_path.exists():
        ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = hooks_path.with_suffix(f".json.bak-pre-kb-{ts}")
        backup.write_text(hooks_path.read_text())

    hooks_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = hooks_path.with_suffix(".json.new")
    tmp.write_text(json.dumps(current, indent=2))
    json.loads(tmp.read_text())  # validate
    tmp.replace(hooks_path)

    print(json.dumps({
        "hooks_json": str(hooks_path),
        "hooks_added": added_cmds,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
