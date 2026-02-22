---
description: Guide for using Model Context Protocol (MCP) tools for BigQuery and GitHub
---

# MCP Integration Workflow

This guide prescribes how agents (`@data-engineer`, `@bi-analyst`, `@orchestrator`) should utilize the available MCP servers to enhance automation and context gathering.

## 1. BigQuery MCP (`@data-engineer`, `@bi-analyst`)

### **Schema Validation (Pre-Change)**
Before modifying any `sqlx` definition, the **Data Engineer** MUST verify the existing schema in BigQuery to prevent breaking changes.

**Tool:** `mcp_bigquery_get_table_info`
**Usage:**
```python
# Example: Check schema of members table before adding columns
get_table_info(project="your-project-id", dataset="bronze_dataset", table="members")
```

### **Data Impact Analysis**
When investigating anomalies or validating data loads (e.g., after `generate_test_data.py`), use the analysis tools.

**Tool:** `mcp_bigquery_ask_data_insights`
**Usage:**
"Analyze the distribution of 'ministry' values in the silver.members table."

### **Read-Only Queries**
Agents are authorized to run `SELECT` queries to verify data states. **DROP/DELETE/UPDATE/INSERT are strictly prohibited via MCP.**

**Tool:** `mcp_bigquery_execute_sql`
**Usage:**
```sql
SELECT count(*) FROM `project.dataset.table` WHERE created_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
```

## 2. GitHub MCP (`@orchestrator`)

### **Issue & Duplicate Detection**
Before creating a new task or issue, the **Orchestrator** MUST check for existing work.

**Tool:** `mcp_github-mcp-server_search_issues`
**Usage:**
"Search for open issues related to 'dark mode fixes'"

### **Context Gathering**
To read file contents from the remote repository (useful for checking state on `feature/v2-architecture` branch vs local).

**Tool:** `mcp_github-mcp-server_get_file_contents`
**Usage:**
Get contents of vital configuration files if local copies are suspect.

### **Pull Request Management**
Automating the handover process.

**Tool:** `mcp_github-mcp-server_list_pull_requests`
**Usage:**
Check status of recently created PRs to update the user.
