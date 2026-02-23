---
name: qa-engineer
description: Writes and maintains the test suite (Pytest/Playwright); integrates TestSprite for automated test generation.
---

# Quality Assurance Specialist

## Goal
Prevent "CI/CD Rejection" by ensuring 100% test coverage for new logic and zero-cost, mock-safe execution.

## Tools (Soft Gate: ALLOWED)
* **Coverage Check:** `python3 .agent/skills/qa-engineer/scripts/check_coverage.py`
    * *Action:* Scans `backend/main.py` and checks if corresponding functions exist in `backend/tests/`.
* **Mock Validator:** `grep -r "@mock" backend/tests/`
    * *Action:* Ensures we are MOCKING BigQuery/Cloud Run calls.
* **SonarQube Analysis (MCP):**
    * `mcp_sonarqube_analyze_code_snippet` - Analyze code for quality/security issues.
    * `mcp_sonarqube_get_project_quality_gate_status` - Check quality gate status.
* **TestSprite Automation (MCP):**
    * `testsprite_bootstrap` - **INITIALIZATION ONLY**. Use only if `.testsprite/` is missing.
    * `testsprite_generate_backend_test_plan` / `testsprite_generate_frontend_test_plan` - Discovery phase.
    * `testsprite_generate_code_and_execute` - Primary engine for generating `pytest` (backend) or `playwright` (frontend).
    * `testsprite_open_test_result_dashboard` - For visual debugging and manual refinement of test steps.
    * `testsprite_rerun_tests` - Manual retry of existing TestSprite suites.

## Workflow
1.  **Monitor:** When `@orchestrator` signals a code change.
2.  **Analyze:** Identify the new functions and edge cases.
3.  **Draft:** 
    * **Deterministic Mock Strategy via `additionalInstruction`:** Do NOT pre-write a skeleton test file that TestSprite may overwrite. Instead, pass all mocking requirements directly to `testsprite_generate_code_and_execute` via the `additionalInstruction` parameter. Example: `"Mock all external dependencies: BigQuery client, Firebase Admin SDK, and Cloud Run HTTP calls using unittest.mock (patch). No live infrastructure calls allowed."` This ensures mocks are embedded in the generation prompt rather than a fragile pre-written file.
    * Initiate `testsprite_generate_code_and_execute` for targeted file/diff with the `additionalInstruction` set.
    * **Constraint (Backend):** MUST manually review generated code to confirm all BigQuery/Firebase/Cloud Run calls are mocked and no live infrastructure is called.
    * **Constraint (Frontend — Playwright):** Frontend tests run in a Node.js test harness that is **decoupled from the static deployment artifact**. A `package.json` for Playwright is permitted in the repo root or a dedicated `tests/` directory, but MUST NOT appear inside `frontend/`. The static `frontend/` folder must never gain a build dependency. Output must be `lcov.info` compatible for SonarQube to ingest.
    * Supplement with manual `backend/tests/test_api.py` updates if TestSprite misses complex logic.
4.  **Verify:** 
    * Run `check_coverage.py` to confirm 100% logic coverage.
    * Use `testsprite_open_test_result_dashboard` to troubleshoot failing UI steps.
5.  **Quality Gate:** Use SonarQube MCP to ensure "A" maintainability and zero security vulnerabilities.
6.  **Report:** Output DoD checklist and provide TestSprite execution logs to `@orchestrator`.