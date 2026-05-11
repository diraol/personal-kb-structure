"""CLI entrypoints exposed via pyproject.toml scripts."""
from __future__ import annotations
import datetime as dt
import json
import re
import sys
from pathlib import Path

import click

from kb import indexer, search, fts, embed
from kb.config import VAULT_DIR


@click.command(name="kb-index")
@click.option("--full", is_flag=True, help="Drop and rebuild all indexes.")
@click.option("--no-embeddings", is_flag=True, help="Skip semantic embeddings (FTS only).")
@click.option("--path", "paths", multiple=True, type=click.Path(path_type=Path),
              help="Index specific path(s) only. Repeatable.")
def index_cmd(full: bool, no_embeddings: bool, paths: tuple[Path, ...]):
    """Build / refresh the keyword and semantic indexes."""
    if not no_embeddings:
        ok, msg = embed.health()
        if not ok:
            click.echo(f"[warn] Ollama not reachable ({msg}). Indexing FTS only.", err=True)
            no_embeddings = True
    stats = indexer.reindex(
        paths=list(paths) if paths else None,
        full=full,
        with_embeddings=not no_embeddings,
    )
    click.echo(json.dumps(stats, indent=2))


@click.command(name="kb-search")
@click.argument("query", nargs=-1, required=True)
@click.option("--type", "note_type", default=None, help="Filter by type.")
@click.option("--project", default=None, help="Filter by project slug.")
@click.option("--tag", default=None, help="Filter by tag.")
@click.option("--limit", default=10, show_default=True)
@click.option("--json", "as_json", is_flag=True)
def search_cmd(query, note_type, project, tag, limit, as_json):
    """Hybrid keyword + semantic search."""
    q = " ".join(query)
    results = search.hybrid_search(
        q, limit=limit, note_type=note_type, project=project, tag=tag,
    )
    if as_json:
        click.echo(json.dumps(results, indent=2, default=str))
        return
    if not results:
        click.echo("No results.")
        return
    for r in results:
        head = f"{r.get('score', 0):.4f}  {r['title']}  ({r['type']}"
        if r.get("project"):
            head += f"/{r['project']}"
        head += f")  — {r['path']}"
        click.echo(head)
        if r.get("section"):
            click.echo(f"    § {r['section']}")
        snip = r.get("snippet") or ""
        if snip:
            click.echo(f"    {snip}")
        click.echo()


@click.command(name="kb-new")
@click.argument("template_name", type=click.Choice(["project", "decision", "gotcha", "reference", "memory", "domain"]))
@click.argument("slug")
@click.option("--project", default=None)
@click.option("--title", default=None)
def new_cmd(template_name, slug, project, title):
    """Scaffold a new note from a template."""
    template_file = {"project": "project-index"}.get(template_name, template_name)
    template_path = VAULT_DIR / "_meta" / "templates" / f"{template_file}.md"
    if not template_path.exists():
        raise click.ClickException(f"Template not found: {template_path}")
    tpl = template_path.read_text(encoding="utf-8")
    today = dt.date.today().isoformat()
    name = title or slug.replace("-", " ").title()

    content = (
        tpl.replace("{{slug}}", slug)
           .replace("{{date}}", today)
           .replace("{{title}}", name)
           .replace("{{name}}", name)
           .replace("{{project}}", project or "")
    )

    if template_name == "project":
        base = VAULT_DIR / "projects" / slug
        base.mkdir(parents=True, exist_ok=True)
        (base / "decisions").mkdir(exist_ok=True)
        (base / "gotchas").mkdir(exist_ok=True)
        (base / "architecture").mkdir(exist_ok=True)
        (base / "sessions").mkdir(exist_ok=True)
        target = base / "_index.md"
    elif template_name == "domain":
        target = VAULT_DIR / "domains" / f"{slug}.md"
    elif template_name == "reference":
        target = VAULT_DIR / "references" / f"{slug}.md"
    elif template_name == "memory":
        target = VAULT_DIR / "memory" / "facts" / f"{slug}.md"
    elif template_name == "decision":
        if not project:
            raise click.ClickException("--project required for decision notes")
        target = VAULT_DIR / "projects" / project / "decisions" / f"{slug}.md"
    elif template_name == "gotcha":
        if not project:
            raise click.ClickException("--project required for gotcha notes")
        target = VAULT_DIR / "projects" / project / "gotchas" / f"{slug}.md"
    else:
        raise click.ClickException("unreachable")

    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise click.ClickException(f"Already exists: {target}")
    target.write_text(content, encoding="utf-8")
    click.echo(str(target))


@click.command(name="kb-watch")
@click.option("--no-embeddings", is_flag=True, help="Skip semantic embeddings on incremental updates.")
def watch_cmd(no_embeddings):
    """Watch the vault and reindex on change."""
    from watchfiles import watch, Change

    if not no_embeddings:
        ok, msg = embed.health()
        if not ok:
            click.echo(f"[kb-watch] Ollama unreachable ({msg}); FTS-only mode.", err=True)
            no_embeddings = True

    click.echo(f"[kb-watch] watching {VAULT_DIR} (Ctrl-C to stop)", err=True)
    stats = indexer.reindex(with_embeddings=not no_embeddings)
    click.echo(f"[kb-watch] initial: {stats}", err=True)

    for changes in watch(str(VAULT_DIR), recursive=True, step=300, debounce=800):
        to_index = []
        to_check_delete = []
        for change_type, path_str in changes:
            p = Path(path_str)
            if p.suffix != ".md":
                continue
            if change_type == Change.deleted:
                to_check_delete.append(p)
            else:
                if p.exists():
                    to_index.append(p)
        if to_check_delete:
            indexer.reindex(with_embeddings=False)
        if to_index:
            stats = indexer.reindex(paths=to_index, with_embeddings=not no_embeddings)
            click.echo(f"[kb-watch] {stats}", err=True)


if __name__ == "__main__":
    sys.argv[0] = "kb"
    raise SystemExit("Run kb-index, kb-search, kb-new, or kb-watch instead.")
