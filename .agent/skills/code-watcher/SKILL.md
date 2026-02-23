---
name: code-watcher
description: Invoked on demand to analyze git diffs for documentation impact.
---

# Code Watcher

## Goal
Analyze the current git diff on demand and report any changes that require documentation updates to `README.md` or `ARCHITECTURE.md`.

## Triggers
- **On-Demand Invocation**: Triggered explicitly by the `@orchestrator`, a CI hook, or the user before documentation reviews or commits. This agent does NOT run as a continuous background process.
- **Diff Analysis**: Uses git diff or script output covering `backend/`, `frontend/`, and `data/`.

## Actions
1. **Fetch Diff**: Execute `.agent/skills/code-watcher/scripts/get_diff.sh` to capture the latest changes.
2. **Analyze**: Identify if the change was logic-based (e.g., altered core execution paths) or style-based (formatting, superficial changes).
3. **Report**: If logic changed, create a standard "Change Artifact" and ping the `@orchestrator`.
   - *Artifact Format*: "[File Path] modified. [Summary of Change]."
   - *Requirement*: Highlight specific changes that mandate updating the `README.md` or `ARCHITECTURE.md`.