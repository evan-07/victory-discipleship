---
description: Standard instructions for evolving the data warehouse schema.
---

# Data Pipeline Evolution Workflow

This workflow ensures the safe evolution of the Medallion Architecture, preventing breaking changes in downstream Looker Studio reports.

## 1. Ingestion (Bronze Layer)
*   **Actor:** `@data-engineer`
*   **Input:** New Data Source (JSON/CSV)
*   **Action:**
    1.  Define the raw table in `data/definitions/1_bronze/`.
    2.  Ensure correct partitioning (by `ingestion_timestamp`).

## 2. Transformation (Silver Layer)
*   **Actor:** `@data-engineer`
*   **Input:** Bronze Table
*   **Action:**
    1.  **Validation:** Use **BigQuery MCP** (`mcp_bigquery_get_table_info` / `mcp_bigquery_execute_sql` in read-only mode) to inspect the shape of raw remote data.
    2.  Create SQLX file in `data/definitions/2_silver/`.
    3.  Cleanse data (cast types, handle nulls).
    4.  **Linting:** Run `python3 .agent/skills/data-engineer/scripts/schema_lint.py` to enforce naming conventions.

## 3. Aggregation (Gold Layer) & Safety Check
*   **Actor:** `@data-engineer`
*   **Input:** Silver Table
*   **Action:**
    1.  Create/Update SQLX in `data/definitions/3_gold/`.
    2.  **CRITICAL:** Before finalizing, run `./.agent/skills/data-engineer/scripts/impact_analysis.sh <column_name>` for any changed columns.
    3.  **Gate:** If impact analysis finds Looker dependencies, STOP. Consult User/BI Analyst.

## 3a. Rollback Procedure (Silver or Gold Schema Change Failure)

If a schema change causes Dataform assertion failures in CI/CD:

**Step 1 — Detect:** GitHub Actions Dataform compilation/assertion step fails. `@data-engineer` receives the failure notification and identifies which assertions are failing via the CI/CD log.

**Step 2 — Assess:** Run `dataform compile` (read-only — permitted locally) to identify the failing assertions and affected tables without executing any writes.

**Step 3 — Choose a rollback option (in order of preference):**

**Option A — Revert via new commit (preferred):**
```bash
git revert <commit-hash>
git push origin <feature-branch>
# PR CI/CD auto-triggers re-compilation — confirm assertions pass
```

**Option B — Additive fix (if revert is not feasible):**
Add the missing column or table that the assertion expects, rather than reverting. This preserves the additive-only schema principle. Submit as a new commit on the same PR.

**Option C — Assertion update (only if the assertion logic itself was wrong, not the data):**
Update the assertion SQL in the same PR as the schema change. This requires:
- `@architect` review and "Valid Plan" approval for the assertion change.
- A Decision Log entry in ARCHITECTURE.md §18 documenting why the assertion changed.

**Step 4 — Verification:** Re-run CI/CD. Dataform compilation and all assertions MUST pass before the PR merge is unblocked.

> **Hard rule:** NEVER disable or delete an existing assertion to unblock a failing pipeline. Assertions are data integrity guards. Removing them to bypass a failure is prohibited regardless of urgency — escalate to the user instead.

## 4. Visualization Specification
*   **Actor:** `@bi-analyst`
*   **Prerequisite:** Gold Table is ready (or schema is defined).
*   **Action:**
    1.  Run `python3 .agent/skills/bi-analyst/scripts/generate_looker_spec.py <schema.json>`.
    2.  Customize the generated spec (set chart types, colors).
    3.  Deliver the `Looker Configuration Spec` (Artifact) to the user.

## 5. Documentation
*   **Actor:** `@readme-updater`
*   **Action:** Update Data Dictionary in `README.md` if schema changed significantly.
