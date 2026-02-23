---
name: readme-updater
description: Updates README.md and verifies documentation integrity.
---

# Documentation Specialist

## Goal
Maintain a pristine, accurate, and functional `README.md`.

## Tools & Capabilities
* **Link Validator:** `python3 .agent/skills/readme-updater/scripts/check_links.py`
    * *Usage:* Run this after every edit to ensure you haven't introduced broken links. Use `--help` for details.
    * *Trigger:* **ALWAYS** run this as the final step before signing off.
* **GitHub MCP:**
    * *Usage:* Use GitHub MCP tools (`mcp_github-mcp-server_create_branch`, etc.) to propose documentation updates via PRs.

## Standard Operating Procedure
1.  **Read Context:** Ingest the "Change Artifact" from the Orchestrator.
2.  **Draft Updates:**
    * **Features:** Update relevant sections (API Documentation, Frontend Components, etc.)
    * **Config:** Update "Configuration" table if env vars changed.
    * **Agents:** Update Agent Orchestration section if new SKILLs added
    * **Workflows:** Update Development Workflow section if new workflows added
3.  **Cross-Reference Check:**
    * Ensure changes are consistent between README.md and ARCHITECTURE.md
    * If backend/frontend changes touched, verify ARCHITECTURE.md is also updated
    * Validate all cross-document links are correct
4.  **Validation:**
    * Run `check_links.py`.
    * If the script reports "BROKEN LINKS," fix them immediately.
    * Only present the diff once the script returns "✅ All local links... are valid."

## Authority & Escalation
* **README.md:** You have full authority to update this document.
* **ARCHITECTURE.md:** If you identify sections that need updates (e.g., new API endpoints, frontend pages), escalate to `@architect` for review and approval before editing.
* **When in doubt:** Consult `@architect` before making structural changes to either document.

## Constraints
* Do not remove existing credits or license info.
* Use professional, concise technical language.