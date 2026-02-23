---
name: code-watcher
description: Continuously monitors /src for file modifications and reports them.
---

# Code Watcher

## Goal
Detect changes in the codebase that require documentation updates.

## Triggers
- **Manual Invocation**: Typically triggered by the Orchestrator, CI hooks, or User before documentation reviews or commits.
- **Diff Analysis**: Uses git diff or script output covering `backend/`, `frontend/`, and `data/`.

## Actions
1. **Fetch Diff**: Execute `.agent/skills/code-watcher/scripts/get_diff.sh` to capture the latest changes.
2. **Analyze**: Identify if the change was logic-based (e.g., altered core execution paths) or style-based (formatting, superficial changes).
3. **Report**: If logic changed, create a standard "Change Artifact" and ping the `@orchestrator`.
   - *Artifact Format*: "[File Path] modified. [Summary of Change]."
   - *Requirement*: Highlight specific changes that mandate updating the `README.md` or `ARCHITECTURE.md`.