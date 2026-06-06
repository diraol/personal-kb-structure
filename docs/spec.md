# kb — Specification

Feature Branch: `main`  
Created: 2026-06-06  
Status: Active  
Input: Retroactive specification derived from implemented system

---

## User Scenarios & Testing

### US-1 (P1): Retrieve relevant past context before starting work

**User story:** As a software engineer starting work on a project, I want the AI assistant to automatically have relevant context from my past decisions and notes without me having to paste anything.

**Why P1:** This is the primary value proposition. Without it, the system is just a note-taking app.

**Independent test:** Open a new Claude session in a project directory. Without prompting, verify the assistant references relevant vault content in its first response.

**Acceptance scenarios:**
- Given a project directory with a matching `vault/projects/<slug>/_index.md`, When a Claude session starts, Then the index content is injected as context automatically.
- Given a vault with notes tagged with a project slug, When I ask the assistant about the project, Then it searches the vault and surfaces relevant notes.
- Given no matching project index, When a Claude session starts, Then no error occurs and the assistant works normally.

**Edge cases:** Project slug inference from directory name; special characters in directory names; nested project directories.

---

### US-2 (P1): Capture a decision or gotcha mid-session

**User story:** As an engineer mid-session, I want to save a non-obvious finding or decision to the vault without interrupting my flow.

**Why P1:** The vault is only valuable if capture happens. High-friction capture means notes don't get written.

**Independent test:** Call `kb_capture` with type=gotcha, verify the note appears in `kb_search` results immediately afterward in the same session.

**Acceptance scenarios:**
- Given an active AI session, When I call kb_capture with type, title, and body, Then a note is created in the correct vault path and indexed immediately.
- Given a note was just captured, When I search for its content, Then it appears in results without waiting for the watcher.
- Given a duplicate title (same slugified ID), When I call kb_capture, Then an error is returned instead of overwriting the existing note.

**Edge cases:** Very long titles; special characters in title; project=None (goes to general memory); body with wikilinks to existing notes.

---

### US-3 (P2): Search across all notes with natural language

**User story:** As an engineer, I want to find relevant notes by describing what I'm looking for, even if I don't remember the exact words used.

**Why P2:** Core search feature, but relies on Ollama being available. Degrades to keyword search.

**Independent test:** Index a note about "database connection pooling". Search for "how we handle DB connections" and verify the note ranks highly.

**Acceptance scenarios:**
- Given notes in the vault, When I call kb_search with a natural language query, Then results are returned ranked by relevance.
- Given Ollama is unavailable, When I call kb_search, Then FTS-only results are returned with a `_warning` field, not an error.
- Given type and project filters, When I call kb_search, Then only matching notes are returned.

**Edge cases:** Query with FTS5 special characters (handled by ADR-007); empty vault; query longer than embedding context window.

---

### US-4 (P2): Find what links to a given note

**User story:** As an engineer reviewing a decision note, I want to see which other notes reference it, to understand its downstream impact.

**Why P2:** Useful for navigating connected context; depends on wikilink authoring discipline.

**Independent test:** Create two notes where note B has `[[note-a-id]]` in its body. Call `kb_related("note-a-id")` and verify note B appears.

**Acceptance scenarios:**
- Given notes with wikilinks, When I call kb_related with a note ID, Then all notes containing `[[that-id]]` are returned.
- Given a note with no inbound links, When I call kb_related, Then an empty list is returned (not an error).

---

### US-5 (P3): Notes are automatically reindexed on save

**User story:** As an engineer editing notes directly in a text editor, I want changes to be searchable within a few seconds without running any command.

**Why P3:** Useful quality-of-life; requires systemd watcher. Captured notes (US-2) are indexed immediately regardless.

**Independent test:** Edit a note in the vault. Within 5 seconds, verify the changed content is searchable via kb_search.

**Acceptance scenarios:**
- Given the kb-watch.service is running, When I save a markdown file in the vault, Then it is reindexed within ~5 seconds (800ms debounce + processing).
- Given a note is deleted from the vault, When the watcher next cycles, Then the note is removed from search results.

---

## Requirements

### Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-001 | The system MUST support hybrid keyword + semantic search returning ranked results per note. |
| FR-002 | The system MUST support FTS-only mode when Ollama is unavailable. |
| FR-003 | The system MUST expose all tools via MCP (kb_search, kb_get, kb_recent, kb_related, kb_capture, kb_list_projects). |
| FR-004 | The MCP server MUST start in stdio mode without any external dependencies beyond Python. |
| FR-005 | Notes captured via kb_capture MUST be searchable within the same MCP session. |
| FR-006 | The index MUST be fully rebuildable from the vault with `kb-index --full`. |
| FR-007 | The install process MUST be idempotent. |
| FR-008 | Vault content MUST NOT be transmitted to any external network service. |

### Key Entities

**Note**
- `id`: string, kebab-case slug (derived or explicit)
- `type`: enum {project, domain, reference, memory, decision, gotcha, meta}
- `title`: string
- `body`: markdown string
- `tags`: string[]
- `project`: string | null (project slug)
- `created`, `updated`: ISO date
- `status`: enum {active, archived}

**Chunk** (index artifact)
- `note_id`: FK → Note.id
- `chunk_seq`: int (0-based position within note)
- `section`: string | null (H2 heading text)
- `text`: string (chunk body)

---

## Success Criteria

| ID | Criterion |
|----|-----------|
| SC-001 | `kb_search` returns results within 2 seconds for a vault of 1000 notes. |
| SC-002 | `kb_capture` creates and indexes a note within 3 seconds. |
| SC-003 | `kb-index --full` completes within 60 seconds for a 500-note vault with embeddings. |
| SC-004 | The MCP server responds to `initialize` within 2 seconds of process start. |
| SC-005 | `bin/kb-health` reports all checks passed on a correctly configured system. |

---

## Assumptions

- The user has Python 3.11+ and `uv` installed.
- Ollama is optional; its absence degrades but does not break the system.
- systemd --user is available on the target machine (Linux). macOS/Windows support is out of scope.
- The vault contains personal notes; multi-user or team vaults are out of scope.
- Notes are authored in markdown; rich text or binary attachments are out of scope.
