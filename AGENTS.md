# AI Agent Team & Routing Matrix

This document defines the agentic workforce for the **Victory Discipleship Member Management System**. It serves as the single source of truth for agent responsibilities and the triggers that invoke them.

## 1. The Expert Team

The system uses a multi-agent workflow coordinated by the `@orchestrator`.

| Agent | Role | Expertise | Key Tools |
| :--- | :--- | :--- | :--- |
| **@orchestrator** | Workflow Manager | Coordinates complex tasks; manages project lifecycle | `generate_context.sh`, GitHub MCP |
| **@architect** | Technical Authority | Enforces standards; validates project structure | `validate_structure.py`, GitHub MCP |
| **@frontend-dev** | Frontend Specialist | Vanilla HTML/CSS/JS; static site generation | `create_page.sh`, GitHub MCP, SonarQube MCP |
| **@backend-dev** | Backend Specialist | Python (FastAPI); Test-Driven Development | `run_tests.sh`, GitHub MCP, SonarQube MCP |
| **@data-engineer** | Data Architect | BigQuery; Dataform; Medallion pipelines | `impact_analysis.sh`, `schema_lint.py`, GitHub MCP, BigQuery MCP |
| **@infra-ops** | Cloud Infrastructure | Terraform; GCP; Cost optimization | `cost_sentinel.sh`, GitHub MCP |
| **@qa-engineer** | Quality Guardian | Pytest; SonarQube; TestSprite automation | `check_coverage.py`, Sonar MCP, TestSprite MCP |
| **@bi-analyst** | Data Visualization | Looker Studio dashboards; data insights | `generate_looker_spec.py`, BigQuery MCP |
| **@readme-updater**| Docs Maintainer | Documentation integrity; link validation | `check_links.py`, GitHub MCP |
| **@code-watcher** | System Monitor | Analyzes diffs for documentation impact | `check_docs_impact.py`, GitHub MCP |

---

## 2. Routing Matrix (Automated Triggers)

Agents are automatically invoked based on the file paths modified in a session. Refer to [persistence.md](.agent/rules/persistence.md) for enforcement rules.

| Path Pattern | Primary Agent | Secondary Agent(s) |
| :--- | :--- | :--- |
| `backend/**` | `@backend-dev` | `@qa-engineer` |
| `frontend/**` | `@frontend-dev` | `@qa-engineer` |
| `data/definitions/**` | `@data-engineer` | `@bi-analyst` |
| `data/definitions/3_gold/**`| `@data-engineer` | `@bi-analyst` + `@architect` + Looker Impact Statement |
| `terraform/**` | `@infra-ops` | `@architect` |
| `resources/**` | `@infra-ops` | — |
| `.github/workflows/**` | `@infra-ops` | `@qa-engineer` |
| `looker/**` | `@bi-analyst` | — |
| `dashboards/**` | `@bi-analyst` | — |
| `README.md` | `@readme-updater` | — |
| `ARCHITECTURE.md` | `@architect` | `@readme-updater` |
| `.agent/workflows/**` | `@readme-updater` | `@orchestrator` |

---

## 3. Workflow Protocols

This section is the **single source of truth** for all available agent slash-command workflows. Descriptions in other docs (e.g., `README.md`) MUST NOT duplicate this list — they should link here instead.

| Workflow | Trigger | Description | Primary Agent(s) |
| :--- | :--- | :--- | :--- |
| `/feature-development` | New feature request | Full cycle: plan → architect gate → delegate → implement → verify → PR | `@orchestrator` |
| `/data-pipeline-evolution` | BQ schema or Dataform change | Impact analysis → Looker Impact Statement → SQLX edit → compile check → PR | `@data-engineer`, `@bi-analyst` |
| `/feature-branch-workflow` | Any code change | Create branch → develop → SonarQube gate → PR → merge | `@orchestrator` |
| `/architecture-audit` | Compliance review request | Validate structure → cross-reference docs → report findings → remediation plan | `@architect`, `@orchestrator` |
| `/mcp-integration` | MCP tool usage | Guide for using BigQuery, GitHub, SonarQube, and TestSprite MCP tools | `@orchestrator` |
| `/sonarqube-quality-gate` | Post-implementation QA | Run analysis → check gate status → fix issues → re-run | `@qa-engineer` |

### Quality Enforcement
All code changes MUST pass the **SonarQube Quality Gate** enforced by `@qa-engineer` before any PR is eligible for merge. See `/sonarqube-quality-gate` for the full procedure.

### Governance
All workflows operate under the rules defined in [`.agent/rules/persistence.md`](.agent/rules/persistence.md). The `@orchestrator` is responsible for enforcing the OP-01 protocol on every task.
