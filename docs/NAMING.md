# Naming Conventions & Consistency Standards

← Part of [ARCHITECTURE.md](../ARCHITECTURE.md)

---

This document is the **authoritative and binding** source for all naming conventions across the Victory Discipleship system. All agents, engineers, and contributors MUST follow these rules. Any deviation requires an `@architect` review and a documented decision in [DECISIONS.md](DECISIONS.md).

> **Enforcement:** These rules are cross-checked by `validate_structure.py` and `schema_lint.py` during every CI/CD run.

---

## 1. Data Architecture (BigQuery & Dataform)

| Element | Convention | Example | Rule |
| :--- | :--- | :--- | :--- |
| **BigQuery Dataset — Bronze** | `victory_bronze` | `victory_bronze` | Actual GCP dataset identifier. Fixed. Never rename. |
| **BigQuery Dataset — Silver** | `victory_silver` | `victory_silver` | Actual GCP dataset identifier. Fixed. Never rename. |
| **BigQuery Dataset — Gold** | `victory_gold` | `victory_gold` | Actual GCP dataset identifier. Fixed. Never rename. |
| **Dataform definitions dir — Bronze** | `data/definitions/1_bronze/` | `data/definitions/1_bronze/stg_persons.sqlx` | Directory prefix in repo only. NOT a BigQuery dataset name. |
| **Dataform definitions dir — Silver** | `data/definitions/2_silver/` | `data/definitions/2_silver/stg_events.sqlx` | Directory prefix in repo only. NOT a BigQuery dataset name. |
| **Dataform definitions dir — Gold** | `data/definitions/3_gold/` | `data/definitions/3_gold/gold_demographics.sqlx` | Directory prefix in repo only. NOT a BigQuery dataset name. |
| **Bronze Table** | `raw_<entity_plural>` | `raw_form_submissions`, `raw_events` | All bronze tables start with `raw_`. |
| **Silver Table** | `<entity_plural>` | `persons`, `events`, `intern_relationships` | Plain, normalized plural nouns. |
| **Silver SQLX File** | `stg_<entity>.sqlx` | `stg_persons.sqlx`, `stg_events.sqlx` | `stg_` prefix distinguishes the transform file from the table it produces. |
| **Silver Pipeline SQLX File** | `<pipeline_name>.sqlx` (no prefix) | `discipleship_pipeline.sqlx` | For Silver-layer SQLX files that perform cross-table logic. No `stg_` prefix. Lives in `data/definitions/2_silver/`. |
| **Gold View** | `vw_<business_domain>` | `vw_member_demographics`, `vw_attendance_trends` | `vw_` prefix explicitly denotes a read-only BigQuery view. |
| **Gold Dimension Table** | `dim_<entity>` | `dim_members`, `dim_ministry_teams` | OLAP-style dimension prefix. |
| **Gold Fact Table** | `fact_<event>` | `fact_attendance`, `fact_event_registrations` | OLAP-style fact prefix. |
| **Gold Aggregate/Report** | `agg_<topic>` or `rpt_<topic>` | `agg_monthly_stats`, `rpt_leader_headcounts` | For pre-aggregated reporting tables. |

> **Disambiguation:** `1_bronze`, `2_silver`, `3_gold` are **directory prefixes** inside `data/definitions/` for Dataform source file organization only. The actual BigQuery dataset identifiers are `victory_bronze`, `victory_silver`, and `victory_gold`. Every reference to a BigQuery dataset (in Terraform, SQLX files, Python code, and API routes) MUST use `victory_bronze`, `victory_silver`, or `victory_gold`.

**SQL Column Conventions:**

| Column Type | Convention | Example |
| :--- | :--- | :--- |
| All columns | `lower_snake_case` | `first_name`, `journey_stage` |
| Timestamps (with time) | `<action>_at` | `created_at`, `enrolled_at`, `submitted_at` |
| Dates (date only) | `<purpose>_date` | `birthdate`, `start_date`, `one2one_date` |
| Boolean flags | `is_<adjective>` | `is_active`, `is_paid`, `is_deleted` |
| Foreign keys | `<referenced_entity>_id` | `person_id`, `event_id`, `group_id` |
| Ingestion partition | `ingestion_timestamp` | Standard Bronze column; required on all raw tables. |

---

## 2. Backend (Python / FastAPI)

| Element | Convention | Example |
| :--- | :--- | :--- |
| **Module / File** | `lower_snake_case.py` | `main.py`, `auth_utils.py`, `bq_client.py` |
| **Class / Pydantic Model** | `PascalCase` | `PersonResponse`, `EventModel`, `SubmitPayload` |
| **Function / Variable** | `lower_snake_case` | `get_person()`, `submit_form()`, `user_id` |
| **Constant / Env Var** | `UPPER_SNAKE_CASE` | `MAX_CAPACITY`, `DEFAULT_TZ`, `PROJECT_ID` |
| **API Route Path** | `/api/<noun_plural>` (kebab-case) | `/api/persons`, `/api/event-registrations` |
| **Test File** | `test_<module>.py` | `test_main.py`, `test_auth_utils.py` |
| **Test Function** | `test_<function>_<scenario>` | `test_get_person_returns_404_when_not_found()` |

> **Constraint:** API route paths MUST use kebab-case (hyphens, not underscores). `/api/person_roles` ❌ → `/api/person-roles` ✅

---

## 3. Frontend (HTML / CSS / JS)

| Element | Convention | Example |
| :--- | :--- | :--- |
| **HTML File** | `kebab-case.html` | `event-registration.html`, `admin-dashboard.html` |
| **CSS File** | `kebab-case.css` | `main.css`, `admin-styles.css` |
| **JS File** | `kebab-case.js` | `admin.js`, `form-handler.js` |
| **JS Variable / Function** | `camelCase` | `fetchUserData()`, `userId`, `submitForm()` |
| **JS Constant** | `UPPER_SNAKE_CASE` | `API_BASE_URL`, `DEFAULT_TIMEOUT` |
| **CSS Class** | `kebab-case` | `btn-primary`, `nav-bar`, `member-card` |
| **HTML `id` Attribute** | `kebab-case` | `submit-button`, `user-form`, `search-input` |

> **Constraint:** The `frontend/` directory MUST contain only `.html`, `.css`, and `.js` files. No `package.json`, `node_modules`, or build tool configuration may exist inside this directory.

---

## 4. Infrastructure (Terraform & GCP)

| Element | Convention | Example |
| :--- | :--- | :--- |
| **Terraform Resource Label** | `lower_snake_case` | `google_cloud_run_service.main_api` |
| **Terraform Variable** | `lower_snake_case` | `var.project_id`, `var.gcp_region` |
| **GCP Resource Name** | `kebab-case` | `victory-backend-svc`, `victory-run-sa` |
| **Cloud Run Service** | `kebab-case` | `victory-backend` |
| **GCP Storage Bucket** | `kebab-case` | `victory-dataform-output` |
| **Pub/Sub Topic** | `<domain>-<event>-topic` | `attendance-events-topic` |
| **Service Account** | `<role>-sa` (kebab-case) | `cloud-run-worker-sa`, `dataform-runner-sa` |
| **Secret Manager Secret** | `kebab-case` | `bq-credentials`, `firebase-api-key` |

---

## 5. Git & CI/CD

| Element | Convention | Example |
| :--- | :--- | :--- |
| **Branch Name** | `<type>/<kebab-case-description>` | `feature/member-search`, `fix/dataform-bug` |
| **Branch Types** | `feature/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/` | See `README.md` Section 3 |
| **Commit Message** | `<type>(<scope>): <short description>` | `feat(api): add person export endpoint` |
| **GitHub Actions Workflow File** | `kebab-case.yaml` | `deploy-backend.yaml`, `sonarqube-analysis.yaml` |
| **GitHub Actions Secret** | `UPPER_SNAKE_CASE` | `WIF_PROVIDER`, `GCP_PROJECT_ID` |

> **Commit Message Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci` — following the [Conventional Commits](https://www.conventionalcommits.org/) specification.

> **Commit Scopes (examples):** `api`, `frontend`, `data`, `infra`, `auth`, `ci`, `arch`, `docs`. The scope `arch` is valid for architecture documentation changes.

> **Branch description:** The description after the type prefix is free-form kebab-case. `feature/v2-architecture` is valid under `feature/` — no separate `architecture/` branch type is needed.

---

## 6. Agent & Script Naming

| Element | Convention | Example |
| :--- | :--- | :--- |
| **Agent Slash Command** | `/<kebab-case>` | `/feature-development`, `/data-pipeline-evolution` |
| **Shell Script** | `<verb>_<noun>.sh` | `cost_sentinel.sh`, `get_diff.sh`, `check_links.sh` |
| **Python Script** | `<verb>_<noun>.py` | `validate_structure.py`, `generate_looker_spec.py` |
| **Agent SKILL file** | `SKILL.md` (uppercase, fixed filename) | `.agent/skills/backend-dev/SKILL.md` |
| **SKILL.md `name` field** | `kebab-case` | `backend-dev`, `data-engineer`, `bi-analyst` |

> **SKILL.md file naming disambiguation:** The agent configuration file is always named `SKILL.md` (all-caps). The `kebab-case` convention applies exclusively to the `name:` field in the YAML front-matter, not the filename itself.

---

*Section added: 2026-02-23. Last updated: 2026-02-24. Owner: @architect.*
