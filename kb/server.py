"""MCP server exposing the kb vault to Claude Code.

Tools:
  kb_search          — hybrid (FTS5 + semantic) retrieval
  kb_get             — fetch a note by id
  kb_recent          — recently updated notes
  kb_related         — backlinks for a note id
  kb_capture         — append a new note (memory/decision/gotcha/reference)
  kb_list_projects   — enumerate project slugs

Run via stdio (default, per-session):
  uv run kb-server

Run as shared HTTP daemon (recommended for multi-session):
  uv run kb-server --transport http [--port 3333]
"""
from __future__ import annotations
import argparse
import asyncio
import contextlib
import datetime as dt
import json
import os
import re
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from kb import fts, search
from kb.config import VAULT_DIR, VALID_TYPES


app = Server("kb")

_CAPTURE_TYPES = {"memory", "decision", "gotcha", "reference"}


def _slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or dt.datetime.utcnow().strftime("note-%Y%m%d-%H%M%S")


def _capture_target(note_type: str, slug: str, project: str | None) -> Path:
    if note_type == "memory":
        return VAULT_DIR / "memory" / "facts" / f"{slug}.md"
    if note_type == "reference":
        return VAULT_DIR / "references" / f"{slug}.md"
    if note_type == "decision":
        base = VAULT_DIR / "projects" / project / "decisions" if project else VAULT_DIR / "memory" / "decisions"
        return base / f"{slug}.md"
    if note_type == "gotcha":
        base = VAULT_DIR / "projects" / project / "gotchas" if project else VAULT_DIR / "memory" / "facts"
        return base / f"{slug}.md"
    raise ValueError(f"unsupported capture type: {note_type}")


def _build_note(note_type: str, title: str, body: str, *, project: str | None,
                tags: list[str], sources: list[str], related: list[str]) -> str:
    today = dt.date.today().isoformat()
    slug = _slugify(title)
    fm_lines = [
        "---",
        f"id: {note_type}-{slug}",
        f"type: {note_type}",
        f"title: {title}",
    ]
    if project:
        fm_lines.append(f"project: {project}")
    fm_lines += [
        f"tags: [{', '.join(tags)}]" if tags else "tags: []",
        f"sources: [{', '.join(sources)}]" if sources else "sources: []",
        f"related: [{', '.join(related)}]" if related else "related: []",
        f"created: {today}",
        f"updated: {today}",
        "status: active",
        "---",
        "",
        f"# {title}",
        "",
        body.strip(),
        "",
    ]
    return "\n".join(fm_lines)


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="kb_search",
            description=(
                "Hybrid keyword + semantic search across the kb vault. Returns ranked "
                "note chunks with title, path, type, project, section, snippet. Use this BEFORE "
                "asking the user for project context — the vault likely already has it."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural-language or keyword query."},
                    "type": {"type": "string", "enum": sorted(VALID_TYPES),
                             "description": "Filter by note type."},
                    "project": {"type": "string", "description": "Filter by project slug."},
                    "tag": {"type": "string", "description": "Filter by tag."},
                    "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="kb_get",
            description="Fetch a full note by id. Returns frontmatter + body.",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"],
            },
        ),
        Tool(
            name="kb_recent",
            description="Recently updated notes. Useful at session start to see what's hot.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
                    "project": {"type": "string"},
                },
            },
        ),
        Tool(
            name="kb_related",
            description="Notes that link to the given note id (backlinks via wikilinks).",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"],
            },
        ),
        Tool(
            name="kb_list_projects",
            description="List all known project slugs with note counts.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="kb_capture",
            description=(
                "Create a new note in the vault. Use for memory (cross-session facts), decision "
                "(ADR-style), gotcha (non-obvious behavior), or reference (pointer to external)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": sorted(_CAPTURE_TYPES)},
                    "title": {"type": "string"},
                    "body": {"type": "string",
                             "description": "Markdown body (without the H1, which is added)."},
                    "project": {"type": "string", "description": "Project slug, if scoped."},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "sources": {"type": "array", "items": {"type": "string"}},
                    "related": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["type", "title", "body"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "kb_search":
            results = search.hybrid_search(
                arguments["query"],
                limit=arguments.get("limit", 10),
                note_type=arguments.get("type"),
                project=arguments.get("project"),
                tag=arguments.get("tag"),
            )
            return [TextContent(type="text", text=json.dumps(results, indent=2, default=str))]

        if name == "kb_get":
            con = fts.connect()
            try:
                note = fts.get_note(con, arguments["id"])
            finally:
                con.close()
            if not note:
                return [TextContent(type="text", text=json.dumps({"error": "not found"}))]
            abs_path = VAULT_DIR / note["path"]
            note["content"] = abs_path.read_text(encoding="utf-8") if abs_path.exists() else None
            return [TextContent(type="text", text=json.dumps(note, indent=2, default=str))]

        if name == "kb_recent":
            con = fts.connect()
            try:
                rows = fts.recent(con, limit=arguments.get("limit", 10), project=arguments.get("project"))
            finally:
                con.close()
            return [TextContent(type="text", text=json.dumps(rows, indent=2, default=str))]

        if name == "kb_related":
            con = fts.connect()
            try:
                rows = fts.backlinks(con, arguments["id"])
            finally:
                con.close()
            return [TextContent(type="text", text=json.dumps(rows, indent=2, default=str))]

        if name == "kb_list_projects":
            con = fts.connect()
            try:
                rows = fts.list_projects(con)
            finally:
                con.close()
            return [TextContent(type="text", text=json.dumps(rows, indent=2, default=str))]

        if name == "kb_capture":
            note_type = arguments["type"]
            title = arguments["title"]
            project = arguments.get("project")
            target = _capture_target(note_type, _slugify(title), project)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                return [TextContent(type="text",
                                    text=json.dumps({"error": f"already exists: {target}"}))]
            content = _build_note(
                note_type, title, arguments["body"],
                project=project,
                tags=arguments.get("tags", []),
                sources=arguments.get("sources", []),
                related=arguments.get("related", []),
            )
            target.write_text(content, encoding="utf-8")
            from kb import indexer
            stats = indexer.reindex(paths=[target], with_embeddings=True)
            return [TextContent(type="text", text=json.dumps({
                "path": str(target.relative_to(VAULT_DIR)),
                "indexed": stats,
            }, indent=2))]

        return [TextContent(type="text", text=json.dumps({"error": f"unknown tool: {name}"}))]
    except Exception as e:
        return [TextContent(type="text",
                            text=json.dumps({"error": f"{type(e).__name__}: {e}"}))]


async def _run():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())


class _McpAsgiApp:
    """Thin ASGI wrapper around StreamableHTTPSessionManager."""
    def __init__(self, manager) -> None:
        self._manager = manager

    async def __call__(self, scope, receive, send) -> None:
        await self._manager.handle_request(scope, receive, send)


async def _run_http(port: int) -> None:
    import uvicorn
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

    manager = StreamableHTTPSessionManager(app=app, stateless=False, session_idle_timeout=1800)

    async def health(_req):
        return JSONResponse({"status": "ok", "port": port})

    @contextlib.asynccontextmanager
    async def lifespan(_app):
        async with manager.run():
            yield

    starlette_app = Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Mount("/mcp", _McpAsgiApp(manager)),
        ],
        lifespan=lifespan,
    )
    config = uvicorn.Config(starlette_app, host="127.0.0.1", port=port, log_level="warning")
    await uvicorn.Server(config).serve()


def main() -> None:
    p = argparse.ArgumentParser(description="kb MCP server")
    p.add_argument("--transport", choices=["stdio", "http"], default="stdio",
                   help="Transport mode (default: stdio)")
    p.add_argument("--port", type=int, default=int(os.environ.get("KB_MCP_PORT", "3333")),
                   help="HTTP port (default: 3333, or $KB_MCP_PORT)")
    args = p.parse_args()

    if args.transport == "http":
        asyncio.run(_run_http(args.port))
    else:
        asyncio.run(_run())


if __name__ == "__main__":
    main()
