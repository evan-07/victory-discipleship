---
name: code-watcher
description: Invoked on demand to analyze git diffs for documentation impact.
---

# Code Watcher

## Goal
Analyze the current git diff on demand and report any changes that require documentation updates to `README.md` or `ARCHITECTURE.md`.

## Triggers
- **On-Demand Invocation (primary):** Triggered explicitly by the `@orchestrator`, a CI hook, or the user before documentation reviews or commits.
- **Automated Invocation (secondary):** The `/architecture-audit` workflow Phase 2 (automated checks) calls `check_docs_impact.py` directly as a validation step. In this context, the output is captured as part of the audit report, not as a standalone Change Artifact.
- **This agent does NOT run as a continuous background process.** Every invocation is explicit — either on-demand or as a named step in a workflow.
- **Diff scope:** `backend/`, `frontend/`, and `data/` directories.

## Actions
1. **Analyze Impact**: Execute `python3 .agent/skills/code-watcher/scripts/check_docs_impact.py` to analyze changes.
2. **Review Output**: The script will automatically check if changes to `backend/`, `frontend/`, `data/`, or infrastructure trigger a required update for `ARCHITECTURE.md` or `README.md`.
3. **Report**: If the script flags impacts, create a standard "Change Artifact" and ping the `@orchestrator`.
   - *Artifact Format*: "[File Path] modified. [Summary of Change]."
   - *Requirement*: Highlight specific changes that mandate updating the documentation.
4. **GitHub MCP:** Use GitHub MCP tools (`mcp_github-mcp-server_get_file_contents`, `mcp_github-mcp-server_get_commit`) to fetch diffs directly from the remote repository if local diffs are insufficient.