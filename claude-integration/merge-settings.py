#!/usr/bin/env python3
"""Idempotently merge claude-integration/settings.snippet.json into ~/.claude/settings.json.

- Substitutes ${HOME} and ${KB_ROOT} placeholders in the snippet.
- For mcpServers: overwrites the named server (so updates apply).
- For hooks: appends each entry only if the same `command` isn't already wired.
- Always writes a timestamped backup of the original settings file.

Usage:
    python merge-settings.py [--repo <path>] [--settings <path>] [--dry-run]
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
        return {k: substitute(v, env) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [substitute(x, env) for x in obj]
    if isinstance(obj, str):
        out = obj
        for k, v in env.items():
            out = out.replace("${" + k + "}", v)
        return out
    return obj


def merge_hooks(target_hooks: dict, new_hooks: dict) -> tuple[dict, list[str]]:
    """Append hook entries that aren't already present (deduplicated by `command`)."""
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
                   help="Path to the knowldege repo (KB_ROOT).")
    p.add_argument("--settings", default=str(Path.home() / ".claude" / "settings.json"),
                   help="Target settings.json path.")
    p.add_argument("--snippet", default=str(Path(__file__).with_name("settings.snippet.json")),
                   help="Snippet template path.")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    repo = Path(args.repo).resolve()
    snippet_path = Path(args.snippet)
    settings_path = Path(args.settings)

    if not snippet_path.exists():
        sys.exit(f"snippet not found: {snippet_path}")
    if not settings_path.exists():
        sys.exit(f"settings not found: {settings_path}")

    env = {"HOME": str(Path.home()), "KB_ROOT": str(repo)}
    snippet = json.loads(snippet_path.read_text())
    snippet = substitute(snippet, env)
    current = json.loads(settings_path.read_text())

    # mcpServers: overwrite named keys
    current.setdefault("mcpServers", {})
    server_changes = []
    for name, cfg in snippet.get("mcpServers", {}).items():
        if current["mcpServers"].get(name) != cfg:
            server_changes.append(name)
        current["mcpServers"][name] = cfg

    # hooks: idempotent append
    current.setdefault("hooks", {})
    merged_hooks, added_cmds = merge_hooks(current["hooks"], snippet.get("hooks", {}))
    current["hooks"] = merged_hooks

    if args.dry_run:
        print(json.dumps({"mcpServers_set": server_changes, "hooks_added": added_cmds}, indent=2))
        return 0

    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = settings_path.with_suffix(f".json.bak-pre-kb-{ts}")
    backup.write_text(settings_path.read_text())

    tmp = settings_path.with_suffix(".json.new")
    tmp.write_text(json.dumps(current, indent=2))
    json.loads(tmp.read_text())  # validate
    tmp.replace(settings_path)

    print(json.dumps({
        "settings": str(settings_path),
        "backup": str(backup),
        "mcpServers_set": server_changes,
        "hooks_added": added_cmds,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
