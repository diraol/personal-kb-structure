---
id: meta-frontmatter-spec
type: meta
tags: [spec, frontmatter]
created: 2026-05-11
updated: 2026-05-11
---

# Frontmatter spec

Every note under `vault/` must start with YAML frontmatter. The indexer rejects files that fail validation.

## Required fields

| Field      | Type     | Notes                                                                 |
|------------|----------|-----------------------------------------------------------------------|
| `id`       | string   | Slug, kebab-case, unique within the vault. Derive from filename if absent. |
| `type`     | enum     | One of: `project`, `domain`, `reference`, `memory`, `decision`, `gotcha`, `meta`. |
| `created`  | date     | ISO `YYYY-MM-DD`.                                                     |
| `updated`  | date     | ISO `YYYY-MM-DD`. Bump on substantive edits.                          |

## Optional fields

| Field      | Type     | Notes                                                                 |
|------------|----------|-----------------------------------------------------------------------|
| `title`    | string   | Display title. Defaults to the H1 if absent.                          |
| `project`  | string   | Project slug. Required for `type: project` and project-scoped notes. |
| `tags`     | [string] | Free-form. Prefer existing tags (see `tags.md`).                      |
| `aliases`  | [string] | Alternate names for backlinks.                                        |
| `sources`  | [string] | External URLs (Confluence, Jira, Slack permalinks, dashboards).       |
| `related`  | [string] | Wikilink targets, e.g. `[[diplomat-controllers]]`. Indexer follows.   |
| `status`   | enum     | `draft`, `active`, `superseded`, `archived`. Default `active`.        |

## Body conventions

- Start with an H1 matching `title`.
- Use H2 for sections — the chunker splits on H2 boundaries for embedding.
- Wikilinks `[[other-note]]` create backlinks. Aliases supported via `[[other-note|display]]`.
- Code blocks are preserved; the indexer skips them for FTS to avoid keyword noise but includes them in the chunk body.

## Examples

See `vault/_meta/templates/` for ready-to-use scaffolds.
