---
description: Guide for using Model Context Protocol (MCP) tools for BigQuery, GitHub, SonarQube, and TestSprite
---

# MCP Integration Workflow

This guide prescribes how agents should utilize the available MCP servers to enhance automation and context gathering.

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
When investigating anomalies or validating data loads (e.g., after `generate_test_data.py`), use read-only analytical `SELECT` queries. **Do not use `ask_data_insights` or `forecast` tools as they are explicitly disabled in the workspace configuration.**

**Tool:** `mcp_bigquery_execute_sql`
**Usage:**
```sql
SELECT category, COUNT(*) FROM `project.dataset.ministry_catalog` GROUP BY category
```

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

## 3. SonarQube MCP (`@qa-engineer`, `@backend-dev`, `@frontend-dev`)

### **Quality Gate Validation**
Before submitting a Pull Request, agents MUST ensure the codebase meets the Quality Gate.

**Tool:** `mcp_sonarqube_get_project_quality_gate_status`
**Usage:**
Check if the project passes code coverage and maintainability metrics.

### **Issue Remediation**
When a Quality Gate fails, investigate specific code smells or security hot spots.

**Tool:** `mcp_sonarqube_search_sonar_issues_in_projects`
**Usage:**
Search for issues in the project to identify files requiring fixes.

## 4. TestSprite MCP (`@qa-engineer`)

### **Automated Test Generation**
Enhance backend and frontend test coverage autonomously.

**Tool:** `mcp_TestSprite_testsprite_generate_code_and_execute`
**Usage:**
Generate tests for specific components and execute them to verify logic correctness and increase SonarQube coverage metrics.
