# AI Agent Team & Routing Matrix

This document defines the agentic workforce for the **Victory Discipleship Member Management System**. It serves as the single source of truth for agent responsibilities and the triggers that invoke them.

## 1. The Expert Team

The system uses a multi-agent workflow coordinated by the `@orchestrator`.

| Agent | Role | Expertise | Key Tools |
| :--- | :--- | :--- | :--- |
| **@orchestrator** | Workflow Manager | Coordinates complex tasks; manages project lifecycle | `generate_context.sh` |
| **@architect** | Technical Authority | Enforces standards; validates project structure | `validate_structure.py` |
| **@frontend-dev** | Frontend Specialist | Vanilla HTML/CSS/JS; static site generation | `validate_static_page.sh` |
| **@backend-dev** | Backend Specialist | Python (FastAPI); Test-Driven Development | `run_backend_tests.sh` |
| **@data-engineer** | Data Architect | BigQuery; Dataform; Medallion pipelines | `impact_analysis.sh`, `find_lineage.sh` |
| **@infra-ops** | Cloud Infrastructure | Terraform; GCP; Cost optimization | `cost_sentinel.sh` |
| **@qa-engineer** | Quality Guardian | Pytest; SonarQube; TestSprite automation | `check_coverage.py`, Sonar MCP |
| **@bi-analyst** | Data Visualization | Looker Studio dashboards; data insights | `generate_looker_spec.py` |
| **@readme-updater**| Docs Maintainer | Documentation integrity; link validation | `check_links.py` |
| **@code-watcher** | System Monitor | Monitors file changes in `/src` | (Background monitoring) |

---

## 2. Routing Matrix (Automated Triggers)

Agents are automatically invoked based on the file paths modified in a session. Refer to [persistence.md](.agent/rules/persistence.md) for enforcement rules.

| Path Pattern | Primary Agent | Secondary Agent(s) |
| :--- | :--- | :--- |
| `backend/**` | `@backend-dev` | `@qa-engineer` |
| `frontend/**` | `@frontend-dev` | `@qa-engineer` |
| `data/definitions/**` | `@data-engineer` | `@bi-analyst` |
| `data/definitions/3_gold/**`| `@data-engineer` | `@bi-analyst` + `@architect` |
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

### Feature Development
Use the `/feature-development` workflow to trigger the standard implementation cycle.

### Data Evolution
Use the `/data-pipeline-evolution` workflow when modifying BigQuery schemas or Dataform definitions.

### Quality Enforcement
All code changes must pass the **SonarQube Quality Gate** enforced by `@qa-engineer`.
