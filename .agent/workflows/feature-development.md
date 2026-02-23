---
description: Standard instructions for implementing a new feature from idea to production.
---

# Feature Development Workflow

This workflow guides the implementation of a new feature, ensuring strict adherence to the project's Architecture and Quality Standards.

## 1. Planning & Validation (Architect)
*   **Actor:** `@architect`
*   **Input:** User Request (Feature Idea)
*   **Action:**
    1.  Analyze the request against `ARCHITECTURE.md`.
    2.  Run `validate_structure.py` if the user provided specific file paths.
    3.  Create an `implementation_plan.md` detailing:
        *   Schema changes (if any).
        *   Backend Logic & Tests.
        *   Frontend UI components.
*   **Gate:** User MUST approve the plan.

## 2. Backend Implementation (TDD)
*   **Actor:** `@backend-dev`
*   **Prerequisite:** Approved Plan.
*   **Steps:**
    1.  **Scaffold:** Run `python3 .agent/skills/backend-dev/scripts/scaffold_feature.py <feature_name>`.
    2.  **Red (Test):** Edit `backend/tests/test_<feature>.py` to define expected behavior. Run tests to confirm failure.
    3.  **Green (Code):** Implement logic in `backend/main.py` (or new module).
    4.  **Verify:** Run `.agent/skills/backend-dev/scripts/run_tests.sh` until all pass.

## 3. Frontend Implementation
*   **Actor:** `@frontend-dev`
*   **Prerequisite:** Backend API is ready (or mocked).
*   **Steps:**
    1.  **Scaffold:** Run `.agent/skills/frontend-dev/scripts/create_page.sh <page_name>` (if new page).
    2.  **Implement:** Write HTML/JS in `frontend/`. Ensure **NO** build steps required (vanilla JS/CSS).
    3.  **Verify:** Open HTML file locally or use a static server to test UI flow.

## 4. Quality Assurance
*   **Actor:** `@qa-engineer`
*   **Action:**
    1.  Run `python3 .agent/skills/qa-engineer/scripts/check_coverage.py`.
    2.  Use **SonarQube MCP** (`mcp_sonarqube_get_project_quality_gate_status`) to verify pre-merge code quality.
    3.  Use **TestSprite MCP** (`testsprite_generate_code_and_execute`) to automatically backfill missing test coverage or fix flaky tests.
    4.  Verify that no "Real World" API calls are made in tests (must use `@mock`).

### Phase 4 Failure Protocol

If `@qa-engineer` returns FAIL from Phase 4, apply the following recovery paths:

**Coverage failure (< 80%):**
1. `@qa-engineer` runs `testsprite_generate_code_and_execute` with `additionalInstruction` specifying mock targets (BigQuery, Firebase Admin, Pub/Sub).
2. If TestSprite still cannot reach 80%, `@qa-engineer` writes manual pytest tests for the uncovered paths.
3. Loop back to Phase 4 (re-run `check_coverage.py`) — maximum **2 retry cycles** before escalating to the user.

**SonarQube gate failure (security hotspot / code smell / maintainability):**
1. `@qa-engineer` identifies the specific failing rule via `mcp_sonarqube_search_sonar_issues_in_projects`.
2. Routes the fix back to the appropriate agent: `@backend-dev` for Python issues, `@frontend-dev` for JS issues.
3. The implementation agent applies the fix and calls `run_tests.sh` to confirm tests still pass.
4. **Loop back to Phase 2 (Backend) or Phase 3 (Frontend)** — NOT back to Phase 1. The Architect Valid Plan does not require re-approval for a QA-fix loop.
5. `@orchestrator` logs each fix cycle in CSA as a "QA Retry Receipt."

**Maximum retries:** After **3 failed QA cycles** total, `@orchestrator` MUST stop and escalate to the user with the full failure log (coverage report + SonarQube gate status + what was attempted).

## 5. Infrastructure Check (FinOps)
*   **Actor:** `@infra-ops`
*   **Action:**
    1.  If Terraform was modified, run `.agent/skills/infra-ops/scripts/cost_sentinel.sh`.
    2.  Ensure no non-free resources (e.g., Load Balancers, Cloud NAT) were added.

## 6. Documentation
*   **Actor:** `@readme-updater`
*   **Action:**
    1.  Update `README.md` with new features/endpoints.
    2.  Run `check_links.py` to ensure valid documentation.

## 7. Submission
*   **Actor:** `@orchestrator`
*   **Action:** Present the "Definition of Done" checklist to the user.
