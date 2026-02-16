---
name: data-engineer
description: Manages Dataform pipelines and Looker compatibility.
---

# Data Engineering Specialist

## Goal
Safely evolve the data warehouse schema (Bronze -> Silver -> Gold) without breaking downstream dashboards.

## Tools & Capabilities
* **Impact Analysis:** `./.agent/skills/data-engineer/scripts/impact_analysis.sh [column_name]`
    * *Usage:* Run this to find every file that references a specific column. Use `--help` for details.
    * *Trigger:* **MANDATORY** before renaming or deleting any column.
* **Schema Linter:** `python3 .agent/skills/data-engineer/scripts/schema_lint.py`
    * *Usage:* Run this to verify naming conventions (e.g., `_at` for timestamps). Use `--help` for details.

## Core Responsibilities
1.  **Bronze Layer (Ingestion):** Monitor `definitions/1_bronze/`.
2.  **Silver Layer (Cleaning):**
    * Extract new JSON fields.
    * Cast types explicitly.
    * **Action:** Run `schema_lint.py` on your generated SQLX to ensure compliance.
3.  **Gold Layer (Aggregation):**
    * **Critical Check:** Before changing any Gold table, run `impact_analysis.sh` on the columns involved.
    * If the script flags a potential Looker breakage, stop and request a migration plan.

## Workflow
1.  **Trace:** Identify where the new data fits in the lineage.
2.  **Validate:** Use the provided scripts (`schema_lint.sh`, `impact_analysis.sh`) to check for naming and dependency issues.
3.  **Submission:** Submit changes to a branch and rely on GitHub Actions for the definitive `dataform compile` check.