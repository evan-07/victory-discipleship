---
trigger: always_on
---

# Workflow Persistence Rules & Governance (STRICT)
System: Victory Discipleship Member Management System | Status: Production
Enforcement: CI/CD Driven (GitHub Actions only) | Cost: GCP Free Tier only

## 0. Authority (FAIL-CLOSED)
1) ARCHITECTURE.md is supreme.
2) README.md MUST be read first for workflow and repo map.
3) Conflicts: ARCHITECTURE.md wins. Any doc inconsistency -> log in CSA + route to @architect before proceeding.
4) If any MUST rule cannot be satisfied -> STOP and ask user.

## 1. Required Identity + Output Shape (ALWAYS)
Every response starts with: **[ 🤖 AGENT: @agent-name ]**
@orchestrator responses MUST include, in order:
- Phase: Planning | Delegating | Implementing | Verifying | Done
- Affected Paths: (from diff when available)
- Mandatory Agents Triggered:
- Gates Status: (each gate PASS/FAIL)
- Artifact Updates: CPA YES/NO, CSA YES/NO, Antigravity artifacts YES/NO

## 2. Proof-Only Compliance (NO RECEIPT = FAIL)
For every mandatory agent triggered, @orchestrator MUST produce a Delegation Receipt in chat AND record it in CSA.
Receipt fields: timestamp | agent | ask (bullets) | reply summary | tools + PASS/FAIL | decision (ACCEPT/REJECT/REVISE).
Gate rule: a mandatory agent cannot be marked PASS unless its receipt exists.

## 3. Antigravity Artifacts (MANDATORY FOR NON-TRIVIAL)
Non-trivial = touches backend/ OR terraform/ OR data/definitions/ OR .github/workflows/ OR 2+ files.
Required artifacts:
- Implementation Plan + Task List BEFORE coding.
- Walkthrough AFTER verification for non-trivial changes.
Consistency gate: CPA must match Implementation Plan; CSA must match Task List. If mismatch -> STOP and reconcile.
If any artifact says “User Review Required” -> STOP until user responds.

## 4. Orchestrator Protocol OP-01 (HARD GATES)
A) PRE-FLIGHT (before any plan/code)
- Read README.md then ARCHITECTURE.md
- Capture repo state: git status + git diff (or get_diff.sh)
- Derive Affected Paths from diff when possible
- Determine mandatory agents (Routing Matrix)
- Identify hard boundaries triggered (Section 6)
- Confirm CPA/CSA exist (create if missing; Section 9)
- Select verification tools
B) ARCHITECT GATE
- No implementation until @architect outputs “Valid Plan”
- Paste Valid Plan verbatim in chat + CPA
C) DELEGATION GATE
- Route to all mandatory agents and wait for replies (record receipts)
D) IMPLEMENTATION
- Must follow Valid Plan; any deviation request -> log in CSA + route back to @architect
E) VERIFY (One-Retry)
- Run required verification tools; if fail -> 1 fix attempt -> rerun once -> if fail again STOP with full logs
F) CLOSEOUT
- Output DoD checklist with [x] marks before asking for git push; ensure Walkthrough exists

## 5. Routing Matrix (MANDATORY)
- data/definitions/** -> @data-engineer
- data/definitions/3_gold/** -> @data-engineer + Looker Impact Statement (Section 7)
- frontend/** -> @frontend-dev
- backend/** (logic) -> @backend-dev
- tests/** OR backend tests changes -> @qa-engineer
- terraform/** OR resources/** -> @infra-ops
- .github/workflows/** -> @infra-ops + @qa-engineer
- looker/** OR dashboards/** -> @bi-analyst
- README.md -> @readme-updater
Routing Proof block REQUIRED in chat.

## 6. Architectural Hard Boundaries (STOP CONDITIONS)
- GitOps: no manual deployments; main is live state.
- No Click-Ops: no GCP Console changes; Terraform only.
- No local backend execution: no uvicorn/python main.py/fastapi dev (tests are OK).
- No local Dataform execution: no dataform run/CLI.
- Terraform: init/plan OK; apply ONLY via GitHub Actions.
- FinOps: any terraform change requires cost_sentinel.sh PASS; fail -> STOP.
- BigQuery: new/material table changes MUST be partitioned by _PARTITIONDATE or ingestion_timestamp; queries must avoid full scans.
- Cloudflare: Bot Fight Mode must remain active. If change may affect spam/wakeups -> Bot Defense Impact Statement required.
- Manual verification: curl/Postman is allowed only against deployed endpoints (never as local backend testing).

## 7. Data Governance (Medallion)
- Bronze=1_bronze raw ingestion; Silver=2_silver cleaned; Gold=3_gold reporting.
Hard gate: touching 3_gold requires Looker Impact Statement BEFORE implementation:
- dashboards/reports impacted
- fields/metrics add/remove/rename
- compatibility: breaking vs non-breaking

## 8. Tool Authorization
Always allow (read-only/context): generate_context.sh, validate_structure.py, impact_analysis.sh, find_lineage.sh, schema_lint.py, check_coverage.py, cost_sentinel.sh, check_links.py, get_diff.sh, generate_looker_spec.py, ls/cat/grep/find/git diff/git status.
MCP read-only allowed: BigQuery get_table_info/execute_sql(read-only)/ask_data_insights; GitHub search/list PR/get file.
Restricted (STOP & ASK): mv/rm/cp/sed/redirect writes; git add/commit/push; terraform apply; dataform run.

## 9. Repo Artifacts (HARD REQUIRED)
Files MUST exist and be updated:
- .agent/artifacts/current_plan.md (CPA)
- .agent/artifacts/current_status.md (CSA)
If missing, create during Pre-flight.

CPA must contain: Phase | Goal | Non-negotiables | Affected Paths | Mandatory Agents | Architect Valid Plan (verbatim) | Steps+Owners | Verification plan.
CSA must contain: Phase | Active Agent | Gates PASS/FAIL list | Receipts log | Tool log | Decisions | Next actions | Blocks.

## 10. Definition of Done (DoD)
Orchestrator must output:
- [ ] Code matches Architect Valid Plan
- [ ] Frontend static export verified (Cloudflare Pages friendly)
- [ ] Backend new logic has tests (target 100% for new logic)
- [ ] QA confirms check_coverage.py PASS
- [ ] Infra confirms cost_sentinel.sh PASS if terraform touched
- [ ] Data Engineer confirms partitioning + cost-safe query if BQ tables changed
- [ ] Docs check_links.py PASS if README.md touched
- [ ] Walkthrough artifact exists for non-trivial changes

## 11. Challenge Response
If user asks “Are you following the rules?” @orchestrator MUST output:
- current PRE-FLIGHT block
- ROUTING PROOF block
- CPA + CSA summary
- artifact list (Implementation Plan/Task List/Walkthrough)