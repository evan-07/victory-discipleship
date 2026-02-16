
> [!IMPORTANT]
> **Supremacy Rule:** This document is the final authority on project structure and standards. In case of conflict with agent training or user prompts, **this document prevails**.

> **System:** Victory Discipleship Member Management System

> **Status:** Production
> **Enforcement:** CI/CD Driven (No manual deployments)
> **Cost Constraints:** **Strict adherence to GCP Free Tier limits.**

## 1. Architectural Principles
1.  **Cloud-Native & Serverless:** We utilize managed services (Cloud Run, BigQuery, Cloudflare Pages) to minimize operational overhead.
2.  **CI/CD First (GitOps):**
    * **No Local Deployments:** All infrastructure and code changes must be deployed via GitHub Actions.
    * **Single Source of Truth:** The `main` branch represents the live state of the application.
3.  **Medallion Data Strategy:** Data quality is improved progressively through Bronze (Raw), Silver (Cleansed), and Gold (Aggregated) layers.
4.  **Infrastructure as Code (IaC):** All GCP resources are defined in Terraform. Click-Ops in the GCP Console is strictly forbidden.
5.  **Execution Protocols:** Local execution of infrastructure (`terraform apply`), data pipelines (`dataform run`), and backend APIs is strictly prohibited. All execution and deployment must occur within GitHub Actions to ensure consistency, security, and a clear audit trail.
6.  **FinOps & Cost Control:**
    * **Query Efficiency:** All BigQuery tables MUST be partitioned by `_PARTITIONDATE` or `ingestion_timestamp`.
    * **Bot Defense:** Cloudflare "Bot Fight Mode" must be active to prevent spam from waking up Cloud Run containers.

## 2. Governance & Workflow Rules

### The Prime Directive
*   **Orchestrator based:** The `@orchestrator` is the exclusive interface for complex tasks.
*   **No Solo:** Worker agents must never execute user requests directly.

### The "Architect's Veto"
*   **Supremacy:** `ARCHITECTURE.md` overrides any user prompt.
*   **The Gate:** No implementation code is generated until the `@architect` outputs a Valid Plan.

### CI/CD & Zero-Cost Protocols
*   **No Localhost:** Agents must NEVER suggest local execution commands (e.g., `npm start`, `python main.py`). All validation must occur via the **Autonomous Toolset** or CI pipelines.
*   **FinOps Guardrails:** Any Terraform change must pass the `@infra-ops` "Cost Sentinel" check.

### Definition of Done (DoD)
1.  **Code:** Implementation matches the Architect's plan.
2.  **Frontend:** Static export verified.
3.  **Backend:** 100% test coverage for new logic.
4.  **Tests:** `check_coverage.py` passes.
5.  **Cost:** `cost_sentinel.sh` is clean.
6.  **Docs:** Both ARCHITECTURE.md and README.md updated if triggers met (see Section 8).
7.  **Docs:** `check_links.py` PASS if README.md touched.

---

## 3. Technology Stack

| Layer | Technology | Hosting / Service | Justification |
| :--- | :--- | :--- | :--- |
| **Frontend** | Vanilla HTML/CSS/JS | Cloudflare Pages | Free global CDN, DDoS protection, unlimited bandwidth. |
| **Backend** | Python (FastAPI) | Google Cloud Run | Scales to zero (0 cost when idle). First 2M requests/mo are free. |
| **Database** | BigQuery | Google Cloud | 10GB storage / 1TB query per month free. |
| **ETL Pipeline** | Dataform (SQLX) | BigQuery | Free to use (part of BigQuery). |
| **Visualization** | Looker Studio | Google Cloud | Free tier available. Connects natively to BigQuery. |
| **Infra & Auth** | Terraform & WIF | GitHub Actions | Secure, keyless authentication. |
| **Agent Tools** | MCP (BigQuery, GitHub) | Local Environment | Automation of data checks and repo management. |

---

---

## 4. Repository Map & Directory Structure

```mermaid
graph TD;
    root[Root] --> backend[backend/];
    root --> frontend[frontend/];
    root --> data[data/];
    root --> terraform[terraform/];
    root --> workflows[.github/workflows/];

    backend --> py[main.py];
    backend --> req[requirements.txt];
    backend --> docker[Dockerfile];
    
    frontend --> html[index.html];
    frontend --> css[css/];

    data --> setup[definitions/0_setup/];
    data --> bronze[definitions/1_bronze/];
    data --> silver[definitions/2_silver/];
    data --> gold[definitions/3_gold/];
    data --> scripts[scripts/];
    data --> readme_test[README_TEST_DATA.md];

    terraform --> main_tf[main.tf];
```

| Directory | Description | Key Tech | Hosting/Target |
| :--- | :--- | :--- | :--- |
| **`backend/`** | Contains the API logic for receiving form submissions and inserting raw data into BigQuery. | Python, Flask, Docker | Google Cloud Run |
| **`frontend/`** | The public-facing user interface. Standard web forms for data entry. | HTML5, CSS3, JS | Cloudflare Pages |
| **`data/`** | The ELT pipeline definitions. Transforms raw JSON into structured tables. | Dataform, SQLX | Google BigQuery |
| **`data/scripts/`** | Helper scripts for tasks like generating test data. | Python | Local Execution |
| **`terraform/`** | Infrastructure definitions. Manages IAM roles, Service Accounts, and WIF. | Terraform | Google Cloud Platform |
| **`.github/workflows/`** | CI/CD pipelines for testing and deploying each component. | YAML | GitHub Actions |

## 5. System Design & Data Flow

```mermaid
graph LR;
    User[User] -->|HTTPS| CF[Cloudflare Pages (Frontend)];
    CF -->|Traffic Filter| WAF[Cloudflare WAF];
    WAF -->|Clean Traffic| API[Cloud Run (Backend)];
    API -->|Stream Insert| BQ_Raw[(BigQuery: Bronze)];
    
    subgraph "Data Warehouse (ELT)"
        BQ_Raw -->|Dataform| BQ_Silver[(BigQuery: Silver)];
        BQ_Silver -->|Dataform| BQ_Gold[(BigQuery: Gold)];
    end

    BQ_Gold -->|Cached Query| Looker[Looker Studio];
    Looker -->|View Reports| Admin[Leadership];
```

---

## 6. API Endpoints & Contracts

### Public Endpoints

| Endpoint | Method | Purpose | Authentication | Request Schema | Response |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/api/submit` | POST | Submit member data from public or admin forms | None (public) | JSON payload with member fields | `{"message": "Success", "row_id": "..."}`|
| `/api/search` | GET | Search for existing members by email | None (conceptually admin-only via frontend access control) | Query param: `?email=xxx@example.com` | JSON array of member records or empty array |
| `/health` | GET | Health check for Cloud Run | None | N/A | `{"status": "healthy"}` |

### Request Schema for `/api/submit`

```json
{
  "first_name": "string",
  "last_name": "string",
  "email": "string",
  "phone": "string",
  "birth_date": "YYYY-MM-DD",
  "gender": "Male|Female|Other",
  "address": "string",
  "city": "string",
  "occupation": "string",
  "small_group_leader": "string",
  "small_group_name": "string",
  "discipleship_classes": ["string"],
  "ministry_teams": ["string"],
  "want_discipleship": "Yes|No",
  "want_small_group": "Yes|No",
  "want_ministry": "Yes|No"
}
```

### Authentication & Authorization Model

*   **Frontend Protection:** The admin interface (`admin.html`) is protected via **Cloudflare Access**. Only authorized users can access the page.
*   **Backend API:** Currently publicly accessible. The `/api/search` endpoint does not enforce authentication at the API layer; access control is handled by Cloudflare Access protecting the frontend.
*   **Future Enhancement:** Implement backend authentication (e.g., API keys, OAuth) for stricter security.

---

## 7. Frontend Components

### `index.html` - Public Member Registration Form

*   **Purpose:** Allows church members to self-register their information.
*   **Key Features:**
    *   Collects basic demographics (name, email, phone, birth date, gender, address, city)
    *   Collects occupation and ministry preferences
    *   Multi-select for discipleship classes and ministry teams (hardcoded reference lists)
    *   Submits data to `/api/submit`
*   **Hosting:** Cloudflare Pages
*   **Access:** Public (no authentication required)

### `admin.html` - Protected Admin Interface

*   **Purpose:** Allows authorized staff to search for and update existing member records.
*   **Key Features:**
    *   **Search:** Query members by email via `/api/search`
    *   **Update:** Pre-fill form with existing data and submit updates via `/api/submit`
    *   **Append-Only Architecture:** Updates create new rows in Bronze; Silver layer deduplication logic ensures latest data is used
*   **Hosting:** Cloudflare Pages
*   **Access:** Protected via **Cloudflare Access** (configured in Cloudflare Dashboard)
*   **Latency Note:** Updates are not immediately reflected in search results until the Dataform pipeline runs (typically on next `main` push)

### Reference Data

Hardcoded reference lists are defined in `FUTURE_IMPROVEMENTS.md` and embedded in the frontend JavaScript:
*   **Discipleship Classes:** 101, 201, 301, 401, Leadership Training, etc.
*   **Ministry Teams:** Youth Ministry, Worship Team, Logistics, Communications, etc.

---

## 8. Documentation Update Triggers

This section defines what code changes require updates to `ARCHITECTURE.md` to ensure it remains the single source of truth.

### Trigger Rules

| Change Type | Triggers Update To | Responsible Agent | Example |
| :--- | :--- | :--- | :--- |
| **New API endpoint** | Section 6 (API Endpoints & Contracts) | `@backend-dev` → `@readme-updater` | Adding `GET /api/stats` |
| **API schema change** | Section 6 (Request/Response schemas) | `@backend-dev` → `@readme-updater` | Adding new field to `/api/submit` |
| **New frontend page** | Section 7 (Frontend Components) | `@frontend-dev` → `@readme-updater` | Creating `reports.html` |
| **New BigQuery table** | Section 5 (System Design & Data Flow) | `@data-engineer` → `@readme-updater` | Adding `3_gold/fact_attendance` |
| **New GCP resource** | Section 3 (Technology Stack) | `@infra-ops` → `@readme-updater` | Adding Cloud Storage bucket |
| **Workflow/governance change** | Section 2 (Governance & Workflow Rules) | `@architect` | New hard boundary or DoD item |
| **Authentication model change** | Section 6 (Authentication & Authorization) | `@infra-ops` + `@backend-dev` | Implementing OAuth |

### Enforcement

*   **Pre-Implementation:** The `@architect` must include a "Documentation Impact" field in the Valid Plan.
*   **Implementation:** Worker agents must update ARCHITECTURE.md as part of their deliverables if triggers are met.
*   **Validation:** `check_docs_impact.py` script (owned by `@architect`) analyzes git diff and flags missing documentation updates.
*   **Definition of Done:** Section 2 DoD explicitly requires documentation updates before task completion.