---
name: readme-updater
description: Updates README.md and verifies documentation integrity.
---

# Documentation Specialist

## Goal
Maintain a pristine, accurate, and functional `README.md`.

## Tools & Capabilities
* **Link Validator:** `python3 .agent/skills/readme-updater/scripts/check_links.py`
    * *Usage:* Run this after every edit to ensure you haven't introduced broken links.
    * *Trigger:* **ALWAYS** run this as the final step before signing off.

## Standard Operating Procedure
1.  **Read Context:** Ingest the "Change Artifact" from the Orchestrator.
2.  **Draft Updates:**
    * **Features:** Update the "Features" list.
    * **Config:** Update the "Configuration" table if env vars changed.
3.  **Validation:**
    * Run `check_links.py`.
    * If the script reports "BROKEN LINKS," fix them immediately.
    * Only present the diff once the script returns "✅ All local links... are valid."

## Constraints
* Do not remove existing credits or license info.
* Use professional, concise technical language.