# DevOps, CI/CD & Development Environment

← Part of [ARCHITECTURE.md](../ARCHITECTURE.md) | See also: [SECURITY.md](SECURITY.md) · [API.md](API.md)

---

## 10. CI/CD Pipeline — GitHub Actions + Terraform

Source Control: GitHub | CI/CD: GitHub Actions | IaC: Terraform OSS
### Repository Structure

```plaintext
victory-discipleship/
├── .github/workflows/       # CI/CD (Frontend, Backend, Dataform, Terraform)
├── frontend/                # Cloudflare Pages site (HTML/JS)
│   ├── index.html           # Main VG Leader form
│   ├── admin.html           # Admin portal
│   └── js/                  # Alpine.js logic / Firebase Auth SDK
├── backend/                 # Cloud Run FastAPI application
│   ├── main.py              # API routes & middleware
│   ├── requirements.txt
│   └── Dockerfile
├── data/                    # Dataform definition
│   ├── definitions/
│   │   ├── 1_bronze/        # Bronze staging transforms (stg_*.sqlx)
│   │   ├── 2_silver/        # Silver normalized transforms (stg_*.sqlx)
│   │   └── 3_gold/          # Gold reporting views (gold_*.sqlx)
│   ├── dataform.json        # Dataform config
│   └── package.json
├── terraform/               # Infrastructure as Code
│   ├── main.tf              # Cloud Run, BQ datasets, Pub/Sub
│   ├── vars.tf
│   └── backend.tf           # GCS backend for state
├── .agent/                  # Multi-agent collaboration config
│   ├── skills/              # Specialized agent instructions
│   └── workflows/           # Orchestrator protocols
├── ARCHITECTURE.md          # This document (Source of Truth)
└── README.md                # Dev setup & Workflow guide
```

### GitHub Actions Workflows

- **Frontend:** On push to `main` → Sync `/frontend` to Cloudflare Pages.
- **Backend:** On push to `main` → Build Docker image → Push as `:latest` tag only to Artifact Registry (prior versions pruned by cleanup policy) → Deploy to Cloud Run.
- **Dataform:** On push to `main` → Compile Dataform definitions to validate → Run Dataform assertions. Runtime scheduling is handled by Dataform native `workflow_config` (no deploy step required — the `release_config` picks up the latest `main` commit automatically on its next run).
- **Terraform:** On pull request → `terraform plan`. On merge to `main` → `terraform apply`.
- **SonarCloud:** Every PR runs SonarCloud analysis. Quality Gate failure blocks merge.

#### SonarCloud Quality Gate Conditions:

- Coverage > 80% on new code.
- Duplication < 3%.
- Security Hotspots: 0.
- Maintainability Rating: A.

**Testing Workflow:** The 80% coverage requirement is supported by the `@qa-engineer` agent utilizing **TestSprite**, an automated testing MCP tool. TestSprite autonomously generates, executes, and fixes tests to ensure backend APIs and frontend logic meet the rigorous SonarCloud gates prior to merging.

**Data Testing Workflow:** To ensure the integrity of the data pipeline, the `@data-engineer` agent writes **Dataform Assertions** for every `.sqlx` file. These assertions run automatically during compilation in standard CI/CD and serve as data quality gates before any data is loaded into the `silver` layer or beyond. They enforce hard rules, such as `is_current` validations or schema mapping constraints.

SonarCloud (hosted SonarQube) is free for public GitHub repos. It eliminates the need for a self-hosted SonarQube server.

### Terraform — Resources Managed

Copy
```plaintext
BigQuery
  ├── Datasets: victory_bronze, victory_silver, victory_gold
  ├── Table schemas
  └── Row access policies

Cloud Run
  ├── Service definition
  ├── Environment variables
  ├── Min/max instances, memory allocation
  └── Service account

IAM
  ├── Service accounts (Cloud Run, Looker Studio, Dataform)
  └── Role bindings for each

Artifact Registry
  ├── Docker container registry for Cloud Run images
  └── Cleanup policy: retain `:latest` tag only — prior versions auto-pruned to stay within 0.5 GB free tier

Secret Manager
  └── Secret placeholders (values set manually or via CI)

Dataform
  ├── Repository (Git-connected to GitHub)
  ├── Release config (points to main branch)
  └── Workflow config (hourly cron, Asia/Manila)

Pub/Sub
  └── Topics and subscriptions (attendance → Cloud Function → Dataform)

Cloud Functions
  └── dataform-attendance-trigger (Pub/Sub push subscriber)

Cloudflare
  ├── DNS records
  └── WAF rules (via Cloudflare Terraform provider)
```


## 15. Development IDE — Google AntiGravity
Platform: Local / Agentic Workspace
Google AntiGravity is the primary IDE and agentic AI collaborator used to build, maintain, and iterate on this system.

Why AntiGravity for This Project

- **Agentic coding**: Executes complex, multi-step requests autonomously within safe boundaries.
- **Deep workspace context**: Understands the entire monorepo automatically without requiring manual context building.
- **Rules enforcement**: Adheres strictly to the `ARCHITECTURE.md` and `.agent/rules/persistence.md` guidelines automatically.
- **Artifact tracking**: Maintains planning and execution state across sessions via `.gemini` artifacts and task files.
- **Extensible integrations**: Leverages the Model Context Protocol (MCP) to interact directly with BigQuery, SonarQube, and GitHub directly from the IDE.

(Note: Prior versions of this project used Google Project IDX and Nix environments. This is fully deprecated in favor of AntiGravity.)


## 16. Component Compatibility Matrix
| Component A | Component B | Integration Method | Compatible? |
| :--- | :--- | :--- | :--- |
| Cloudflare Pages | GitHub | OAuth + GitHub Actions deploy action | Yes — Official Cloudflare Pages GitHub Action |
| Cloudflare Pages | Firebase Auth | Firebase JS SDK loaded on page; Cloudflare serves static files | Yes — Firebase SDK is client-side JS |
| Cloudflare WAF | Cloud Run | Cloudflare proxies HTTPS → Cloud Run URL | Yes — Standard reverse proxy |
| Firebase Auth | Cloud Run FastAPI | JWT ID token in Authorization header; Firebase Admin SDK validates | Yes — firebase-admin Python SDK official |
| Cloud Run | BigQuery | google-cloud-bigquery Python client + service account | Yes — Official GCP client library |
| Cloud Run | Secret Manager | google-cloud-secret-manager Python client at startup | Yes — Official GCP client library |
| Cloud Run | Pub/Sub | google-cloud-pubsub Python client publishes on attendance write | Yes — Official GCP client library |
| GitHub Actions | Cloud Run | gcloud run deploy via google-github-actions/deploy-cloudrun | Yes — Official Google GitHub Action |
| GitHub Actions | Cloudflare Pages | cloudflare/pages-action GitHub Action | Yes — Official Cloudflare GitHub Action |
| GitHub Actions | SonarCloud | SonarSource/sonarcloud-github-action | Yes — Official SonarCloud GitHub Action |
| GitHub Actions | Terraform | hashicorp/setup-terraform + terraform apply | Yes — Official HashiCorp GitHub Action |
| Terraform | BigQuery | google_bigquery_dataset, google_bigquery_table resources | Yes — Terraform Google provider |
| Terraform | Cloudflare | cloudflare/terraform-provider-cloudflare | Yes — Official Cloudflare Terraform provider |
| Dataform | BigQuery | Native — Dataform is a BigQuery-native feature | Yes — Same Google product family |
| Dataform | GitHub Actions | gcloud dataform compilationResults + workflowInvocations | Yes — Dataform CLI and REST API |
| Looker Studio | BigQuery | BigQuery connector (native, official) | Yes — First-party Google product integration |
| AntiGravity | GitHub | Native integration via GitHub MCP Server — clone, push, PR from IDE | Yes — MCP extension |
| AntiGravity | BigQuery | Execute SQL and analyze datasets natively via MCP | Yes — MCP extension |
| AntiGravity | SonarQube/SonarCloud | Analyze code logic, quality gates, and specific issues natively | Yes — MCP extension |
| AntiGravity | TestSprite | Generate tests autonomously to fulfill Sonar coverage thresholds | Yes — MCP extension |


---

*Owner: @architect. Last updated: 2026-02-24.*
