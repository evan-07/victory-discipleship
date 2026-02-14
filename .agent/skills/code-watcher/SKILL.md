---
name: code-watcher
description: Continuously monitors /src for file modifications and reports them.
---

# Code Watcher

## Goal
Detect changes in the codebase that require documentation updates.

## Triggers
- **File Save**: Monitor `.ts`, `.js`, `.py`, `.go` files in `/src`.
- **Dependency Change**: Monitor `package.json`, `requirements.txt`.

## Actions
1. **Debounce**: Wait 5 seconds after the last file save event.
2. **Analyze**: Identify if the change was logic-based (requires explanation) or style-based (ignore).
3. **Report**: If logic changed, create a standard "Change Artifact" and ping the `@orchestrator`.
   - *Artifact Format*: "[File Path] modified. [Summary of Change]."