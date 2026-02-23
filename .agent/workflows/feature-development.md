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
