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
