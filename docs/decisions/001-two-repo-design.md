# ADR-001: Two-Repo Design (Structure + Vault)

**Status:** Accepted  
**Date:** 2026-05-11

## Context

The kb project needs to store both infrastructure code (Python, MCP server, CLI, templates) and personal knowledge notes. These have different versioning, sharing, and privacy requirements.

## Decision

Split into two separate git repositories:
- **Structure repo** (`~/kb`): infrastructure, Python code, systemd units, Claude integration — versioned publicly or semi-publicly.
- **Vault repo** (`~/kb/vault`): personal markdown notes — versioned privately, with its own remote.

The structure repo gitignores `vault/projects/`, `vault/domains/`, `vault/memory/`, and `vault/references/`, keeping only `vault/_meta/` (shared templates and schema). The vault repo is cloned into `vault/` as a nested git repo.

## Consequences

- **+** Personal notes never accidentally land in infrastructure commits.
- **+** Can have multiple machines with the same structure repo but different vault remotes.
- **+** Infrastructure updates don't touch note history.
- **−** Two repos to manage; setup requires cloning both.
- **−** Nested git repos can confuse tools that scan for `.git` recursively.
