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

### Script Canonical Locations

All agent scripts live under `.agent/skills/<agent-name>/scripts/`. Always invoke using the full path — relative path invocations are forbidden (working directory at invocation time is not guaranteed).

| Script | Canonical Path | Owner Agent |
| :--- | :--- | :--- |
| `generate_context.sh` | `.agent/skills/orchestrator/scripts/generate_context.sh` | `@orchestrator` |
| `validate_structure.py` | `.agent/skills/architect/scripts/validate_structure.py` | `@architect` |
| `create_page.sh` | `.agent/skills/frontend-dev/scripts/create_page.sh` | `@frontend-dev` |
| `scaffold_feature.py` | `.agent/skills/backend-dev/scripts/scaffold_feature.py` | `@backend-dev` |
| `run_tests.sh` | `.agent/skills/backend-dev/scripts/run_tests.sh` | `@backend-dev` |
| `impact_analysis.sh` | `.agent/skills/data-engineer/scripts/impact_analysis.sh` | `@data-engineer` |
| `schema_lint.py` | `.agent/skills/data-engineer/scripts/schema_lint.py` | `@data-engineer` |
| `cost_sentinel.sh` | `.agent/skills/infra-ops/scripts/cost_sentinel.sh` | `@infra-ops` |
| `check_coverage.py` | `.agent/skills/qa-engineer/scripts/check_coverage.py` | `@qa-engineer` |
| `generate_looker_spec.py` | `.agent/skills/bi-analyst/scripts/generate_looker_spec.py` | `@bi-analyst` |
| `check_links.py` | `.agent/skills/readme-updater/scripts/check_links.py` | `@readme-updater` |
| `check_docs_impact.py` | `.agent/skills/code-watcher/scripts/check_docs_impact.py` | `@code-watcher` |

---

## 2. Routing Matrix (Automated Triggers)

Agents are automatically invoked based on the file paths modified in a session. Refer to [persistence.md](.agent/rules/persistence.md) for enforcement rules.

| Path Pattern | Primary Agent | Secondary Agent(s) |
| :--- | :--- | :--- |
| `backend/**` | `@backend-dev` | `@qa-engineer` |
| `frontend/**` | `@frontend-dev` | `@qa-engineer` |
| `data/definitions/**` | `@data-engineer` | `@bi-analyst` |
| `data/definitions/3_gold/**`| `@data-engineer` | `@bi-analyst` + `@architect` + [Looker Impact Statement](#looker-impact-statement-template) |
| `terraform/**` | `@infra-ops` | `@architect` |
| `resources/**` | `@infra-ops` | — |
| `.github/workflows/**` | `@infra-ops` | `@qa-engineer` |
| `looker/**` | `@bi-analyst` | — |
| `dashboards/**` | `@bi-analyst` | — |
| `README.md` | `@readme-updater` | — |
| `ARCHITECTURE.md` | `@architect` | `@readme-updater` |
| `.agent/workflows/**` | `@readme-updater` | `@architect` |

> **Note on `.agent/workflows/**` routing:** When agent workflow files change, `@readme-updater` updates documentation and `@architect` reviews the change for governance compliance. `@orchestrator` is intentionally NOT listed as secondary — workflow files define `@orchestrator`'s own behavior, so having it self-review creates a logical loop. `@architect` acts as the external reviewer.

> **Note on `/mcp-integration`:** This workflow has no path-based trigger — it is invoked on demand (by user or another agent needing MCP guidance) and does not require a routing matrix entry. It appears in Section 3 for completeness.

---

## 3. Workflow Protocols

This section is the **single source of truth** for all available agent slash-command workflows. Descriptions in other docs (e.g., `README.md`) MUST NOT duplicate this list — they should link here instead.

| Workflow | Trigger | Workflow File | Description | Primary Agent(s) |
| :--- | :--- | :--- | :--- | :--- |
| `/feature-development` | New feature request | `.agent/workflows/feature-development.md` | Full cycle: plan → architect gate → delegate → implement → verify → PR | `@orchestrator` |
| `/data-pipeline-evolution` | BQ schema or Dataform change | `.agent/workflows/data-pipeline-evolution.md` | Impact analysis → Looker Impact Statement → SQLX edit → compile check → PR | `@data-engineer`, `@bi-analyst` |
| `/feature-branch-workflow` | Any code change | `.agent/workflows/feature-branch-workflow.md` | Create branch → develop → SonarQube gate → PR → merge | `@orchestrator` |
| `/architecture-audit` | Compliance review request | `.agent/workflows/architecture-audit.md` | Validate structure → cross-reference docs → report findings → remediation plan | `@architect`, `@orchestrator` |
| `/mcp-integration` | MCP tool usage (on-demand) | `.agent/workflows/mcp-integration.md` | Guide for using BigQuery, GitHub, SonarQube, and TestSprite MCP tools | `@orchestrator` |
| `/sonarqube-quality-gate` | Post-implementation QA | `.agent/workflows/sonarqube-quality-gate.md` | Run analysis → check gate status → fix issues → re-run | `@qa-engineer` |

> **Convention:** Slash commands map 1:1 to files in `.agent/workflows/` using kebab-case. The slash command `/feature-development` invokes `.agent/workflows/feature-development.md`. No further lookup is required.

### Multi-Agent Conflict Resolution

When multiple agents are triggered for the same change (e.g., a Gold schema change triggers `@data-engineer` + `@bi-analyst` + `@architect`), the following sequencing applies:

**Gold schema change sequence:**
1. `@data-engineer` runs first — produces impact analysis and Looker Impact Statement draft.
2. `@bi-analyst` reviews the Looker Impact Statement — approves or requests changes.
3. `@architect` reviews the full plan after both reviews complete — issues "Valid Plan" or rejects.
4. `@orchestrator` records all three receipts before marking the Architect Gate PASS.

**General conflict rule:** When two agents produce contradictory outputs, `@architect` output takes precedence. The conflict is logged in CSA and escalated to the user if it cannot be resolved within the session.

**No parallel implementation:** Multiple agents may analyze in parallel, but only one agent may write code/files at a time. `@orchestrator` serializes the implementation phase.

### Looker Impact Statement Template

Required artifact for any change to `data/definitions/3_gold/**`. `@data-engineer` produces it; `@bi-analyst` must approve it; `@orchestrator` MUST NOT mark the Architect Gate PASS until a completed Looker Impact Statement exists in the CSA receipts log.

A standalone reusable template file is at: `.agent/artifacts/templates/looker_impact_statement_template.md`

```markdown
## Looker Impact Statement

**Date:** YYYY-MM-DD
**PR Branch:** <!-- branch name -->
**Author:** @data-engineer
**Reviewed by:** @bi-analyst (required before merge)

### Change Summary
<!-- One paragraph describing what is changing in the Gold layer -->

### Affected SQLX Files
- `data/definitions/3_gold/gold_XXXX.sqlx`

### Looker Studio Dashboards & Reports Impacted

| Dashboard / Report | Data Source View | Impact Type | Action Required |
|---|---|---|---|
| <!-- e.g. Member Demographics --> | `vw_member_demographics` | None / Breaking / Non-breaking | <!-- e.g. Update date dimension --> |

### Schema Delta

| Field | Action | Data Type | Breaking? |
|---|---|---|---|
| `field_name` | Added / Removed / Renamed from X to Y | STRING / INT64 / BOOL | Yes / No |

### Compatibility Assessment
- [ ] No existing Looker charts use removed/renamed fields
- [ ] New fields are additive (non-breaking)
- [ ] `@bi-analyst` has reviewed and approved Looker configuration updates

### @bi-analyst Sign-off
**Status:** Pending / Approved / Changes Requested
**Notes:**
**Approval Date:**
```

### Quality Enforcement
All code changes MUST pass the **SonarQube Quality Gate** enforced by `@qa-engineer` before any PR is eligible for merge. See `/sonarqube-quality-gate` for the full procedure.

### Governance
All workflows operate under the rules defined in [`.agent/rules/persistence.md`](.agent/rules/persistence.md). The `@orchestrator` is responsible for enforcing the **OP-01 protocol** on every task. OP-01 defines the six mandatory phases (Pre-flight, Architect Gate, Delegation Gate, Implementation, Verify, Closeout) and is fully specified in **Section 4** of [`.agent/rules/persistence.md`](.agent/rules/persistence.md).

---

## 4. Agent Authorization Matrix

This section is the **authoritative source** for what each agent is permitted to do. Individual SKILL.md files MUST NOT contradict this table. In case of conflict, this table governs — escalate to `@architect`.

> **Key:** `YES` = authorized without asking user. `NO` = not authorized (do not use). `ASK USER` = requires explicit user confirmation before acting. `NEVER` = hard prohibition regardless of user instruction.

### 4a. MCP Tool Authorization

| MCP Server | Tool Category | @orchestrator | @architect | @frontend-dev | @backend-dev | @data-engineer | @infra-ops | @qa-engineer | @bi-analyst | @readme-updater | @code-watcher |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **GitHub** | Read (search, list, get file, get commit, list branches, list PRs) | YES | YES | YES | YES | YES | YES | YES | YES | YES | YES |
| **GitHub** | Write (create branch, create/update file, push files, create PR) | YES | NO | YES | YES | YES | YES | NO | NO | YES | NO |
| **GitHub** | Destructive (merge PR, update PR) | ASK USER | NO | NO | NO | NO | NO | NO | NO | NO | NO |
| **BigQuery** | Read-only SELECT queries | NO | NO | NO | NO | YES | NO | NO | YES | NO | NO |
| **BigQuery** | DDL/DML (INSERT, UPDATE, DELETE, DROP, CREATE) | NEVER | NEVER | NEVER | NEVER | NEVER | NEVER | NEVER | NEVER | NEVER | NEVER |
| **SonarQube** | Read (quality gate status, search issues, measures, analyze snippet) | NO | NO | YES | YES | NO | NO | YES | NO | NO | NO |
| **SonarQube** | Write (change issue status, create webhook) | NO | NO | NO | NO | NO | NO | ASK USER | NO | NO | NO |
| **TestSprite** | Generate & execute tests, rerun tests, open dashboard | NO | NO | NO | NO | NO | NO | YES | NO | NO | NO |
| **TestSprite** | Bootstrap (init only, run once) | NO | NO | NO | NO | NO | NO | YES | NO | NO | NO |

### 4b. Code & Infrastructure Permissions

| Action | @orchestrator | @architect | @frontend-dev | @backend-dev | @data-engineer | @infra-ops | @qa-engineer | @bi-analyst | @readme-updater | @code-watcher |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Write code / file edits | NO (delegates only) | NO (plans only) | YES | YES | YES | YES | YES (test files only) | NO | YES (docs only) | NO |
| `git add` / `git commit` / `git push` | ASK USER | NO | ASK USER | ASK USER | ASK USER | ASK USER | ASK USER | NO | ASK USER | NO |
| Create GitHub branch (via MCP) | YES | NO | YES | YES | YES | YES | NO | NO | YES | NO |
| Create GitHub PR (via MCP) | YES | NO | YES | YES | YES | YES | NO | NO | YES | NO |
| Merge GitHub PR | ASK USER | NO | NO | NO | NO | NO | NO | NO | NO | NO |
| Write to BigQuery (via MCP or direct) | NEVER | NEVER | NEVER | NEVER | NEVER | NEVER | NEVER | NEVER | NEVER | NEVER |
| `terraform apply` | NEVER | NEVER | NEVER | NEVER | NEVER | ASK USER | NEVER | NEVER | NEVER | NEVER |
| `dataform run` / `dataform deploy` | NEVER | NEVER | NEVER | NEVER | NEVER | NEVER | NEVER | NEVER | NEVER | NEVER |

> **Rule:** "ASK USER" means the agent MUST stop and request explicit confirmation before performing the action, showing the exact command it intends to run. "NEVER" means the action is prohibited regardless of user instruction — agent must explain why and ask for an alternative approach.
