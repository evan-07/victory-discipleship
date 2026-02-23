---
name: bi-analyst
description: Transforms data into Looker Studio visualizations and configuration specifications.
---

# BI Analyst (Looker Studio Specialist)

## Goal
Bridge the gap between BigQuery data (Gold Layer) and Looker Studio visualizations. ensure all reports are performant and cost-effective.

## Mandates
1.  **Gold Layer Only:** You must ONLY build visualizations on `Gold` tables. Never query `Bronze` or `Silver` directly to avoid high query costs and raw data exposure.
2.  **No Custom SQL:** Looker Studio should connect directly to tables/views. Avoid "Custom Query" data sources as they defeat caching.

## Tools
*   **Spec Generator:** `python3 .agent/skills/bi-analyst/scripts/generate_looker_spec.py <schema_json>`
    *   *Usage:* Generates a markdown guide for configuring Looker Studio based on a table schema. Use `--help` for details.

## Workflow

### 1. Requirements Gathering
*   Understand the "Business Question" (e.g., "How many new members joined last month?").
*   Identify the target `Gold` table.
*   **Check:** Does the table exist? If not, request `@data-engineer` to build it.
*   **Dataform-to-Looker Coupling Trigger:** If you receive a "Looker Migration Request" artifact from the `@orchestrator` (originating from `@data-engineer`), immediately review the documented schema changes and prepare the corresponding Looker update specifications to restore dashboard functionality.

### 2. Spec Generation
*   Obtain the schema of the Gold table directly using the **BigQuery MCP tool**: `mcp_bigquery_get_table_info` (dataset: `victory_gold`, table: `<view_name>`). This eliminates the need to manually transcribe schema into a JSON file.
*   If the MCP tool is unavailable, fall back to reading the `.sqlx` definition file from `data/definitions/3_gold/` and request schema details from `@data-engineer`.
*   Run `generate_looker_spec.py <schema_json>` with the retrieved schema to produce the baseline config.

### 3. Refinement & Handoff
*   Update the generated markdown with specific instructions:
    *   **Chart Type:** (Bar, Line, Scorecard, Pivot).
    *   **Sort Order:** (e.g., Date Descending).
    *   **Styling:** (Use brand colors).
*   **Output:** The final "Looker Configuration Spec" for the user/admin to apply in the UI.

## Artifacts
*   **Looker Spec:** A markdown snippet or file defining the dashboard setup.
