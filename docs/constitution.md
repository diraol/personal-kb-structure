# kb — Constitution

Feature Branch: `main`  
Created: 2026-06-06  
Status: Active

## Purpose

kb is a personal knowledge management system for software engineers who use AI coding assistants. It provides a local, private vault of structured markdown notes with hybrid search, and exposes that vault to AI tools via the Model Context Protocol (MCP).

---

## Core Principles

### 1. Notes are plain markdown — no proprietary formats

All vault content is standard CommonMark with YAML frontmatter. Notes must be readable and editable with any text editor. No binary formats, no database blobs for content. The vault is the source of truth; indexes are derived artifacts.

### 2. Indexes are always rebuildable

The FTS5 SQLite index and LanceDB vector store are generated from the vault. Delete them freely — `kb-index --full` reconstructs everything. Never store canonical data only in the index.

### 3. Semantic search is optional; FTS must always work alone

The system must function without Ollama. If embeddings are unavailable, keyword search continues. Semantic search is an enhancement, not a requirement.

### 4. Capture friction must be near-zero

Adding a note must take one tool call or one command — no multi-step wizards. The MCP `kb_capture` tool is the canonical path from any AI session. Friction kills adoption.

### 5. Privacy by default — nothing leaves the machine

All processing is local: SQLite, LanceDB, Ollama. No cloud APIs for embeddings or search. The vault may contain sensitive personal and professional knowledge; treat it accordingly.

### 6. Vault and infrastructure are separate concerns

Personal notes (vault) live in their own git repo with their own remote. Infrastructure code lives in the structure repo. They are independent — updating kb's code must never require touching note history, and vice versa.

### 7. Degrade gracefully

Every component has a reasonable fallback:
- Ollama unavailable → FTS-only search
- systemd unavailable → stdio MCP server, manual watcher
- Vault repo unavailable → local-only vault, no sync

### 8. Structure over configuration

Prefer conventions over config files. The vault directory layout (`projects/`, `domains/`, `memory/`, `references/`) is the schema. Note type is determined by frontmatter `type:`, not by file location. Minimize knobs.

---

## Non-Negotiables

- Notes MUST be valid UTF-8 markdown files.
- Indexes MUST be rebuildable from the vault with a single command.
- The MCP server MUST start in stdio mode without systemd.
- No vault content MUST be sent to external network services.
- The install process MUST be idempotent (safe to re-run).
