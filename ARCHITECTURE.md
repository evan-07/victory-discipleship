# Victory Church — Master Architecture Plan

**Version:** 4.6 (Compacted Master — Full detail in `docs/`)
**Classification:** Confidential — Internal Use Only
**Scope:** Full-Stack System Design — Frontend, Backend, Data, DevOps, Security, Business Logic & UX


## Document Map

All detailed specifications live in `docs/`. This file is the entry point — read it for orientation, then go to the relevant sub-document.

| Document | Contents |
| :--- | :--- |
| [docs/JOURNEY_STAGES.md](docs/JOURNEY_STAGES.md) | Person lifecycle · 4 journey stages · required fields · stage entry processes · equipping pathway |
| [docs/EVENTS.md](docs/EVENTS.md) | Event taxonomy · 4 categories · category values table |
| [docs/UX_FLOWS.md](docs/UX_FLOWS.md) | Frontend pages · event registration decision tree · 4 scenarios · admin queue · payment flow |
| [docs/UX_FLOWS_PHASE1.md](docs/UX_FLOWS_PHASE1.md) | Phase 1 MVP flows summary and index |
| [docs/UX_FLOWS_PHASE1_REGISTRATION.md](docs/UX_FLOWS_PHASE1_REGISTRATION.md) | Phase 1 event registration scenarios (1.02–1.04) |
| [docs/UX_FLOWS_PHASE1_ADMIN_EVENTS.md](docs/UX_FLOWS_PHASE1_ADMIN_EVENTS.md) | Phase 1 admin event management (1.05–1.06) |
| [docs/UX_FLOWS_PHASE1_ADMIN_PERSONS.md](docs/UX_FLOWS_PHASE1_ADMIN_PERSONS.md) | Phase 1 review queue and person administration (1.07–1.08) |
| [docs/API.md](docs/API.md) | All API routes · auth flow · pre-check logic · discipleship pipeline · write-path ownership matrix |
| [docs/DATA_PIPELINE.md](docs/DATA_PIPELINE.md) | Bronze→Silver→Gold medallion architecture · Dataform transforms · Pub/Sub trigger · data flow diagram |
| [docs/SCHEMA.md](docs/SCHEMA.md) | All Bronze, Silver, and Gold table schemas · dedup algorithm · SCD2 rules |
| [docs/SECURITY.md](docs/SECURITY.md) | 7-layer security · BigQuery row policies · IAM roles · Cloudflare Access |
| [docs/DEVOPS.md](docs/DEVOPS.md) | CI/CD workflows · Terraform resources · IDE setup · component compatibility matrix |
| [docs/REPORTING.md](docs/REPORTING.md) | All 14 Gold views · audience · review_status filter rule · DAG |
| [docs/NAMING.md](docs/NAMING.md) | **Binding** naming conventions — BigQuery, Python, JS, Terraform, Git, agents |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Full architectural decision log |


## 1. Architecture Overview

Victory Church's member and ministry management system is a full-stack, cloud-native application built entirely on free-tier eligible, production-grade services. It manages the full lifecycle of members — from first contact through equipping, intern, and leadership stages — plus event management, equipping pathway tracking, and executive reporting.

### Design Principles

- **Free-tier first.** Every component runs within free-tier limits at current scale.
- **Bronze → Silver → Gold medallion architecture.** Raw data is never mutated. Transformations are versioned SQL.
- **Admin-managed, never auto-computed.** Journey stage, role assignment, and pathway completion are pastoral judgments — the system informs but never replaces human decision-making.
- **Additive schema changes only.** No existing data is ever deleted or migrated destructively.
- **Stateless backend.** Cloud Run scales to zero; all session state is in Firebase Auth JWTs.
- **Completion logic lives in Gold views.** When business rules change, only SQL views are updated — no Silver schema migration required.
- **Duplicate-safe event registration.** The system prevents duplicate event registrations at the API layer.
- **Data sovereignty.** All data resides strictly within GCP Philippines/Taiwan regions. No member PII passes through external SaaS providers.


## 2. Technology Stack Summary

| Layer | Technology | Role | Cost |
| :--- | :--- | :--- | :--- |
| **Edge & Security** | Cloudflare (WAF, CDN, Access) | DDoS protection, WAF, HTTPS termination, routing | Free |
| **Frontend** | Cloudflare Pages | Static site hosting with global CDN, preview URLs, custom domain | Free |
| **Authentication** | Firebase Auth | Google Sign-In + JWT tokens for all personas | Free Spark |
| **Backend API** | Cloud Run (Python / FastAPI) | Stateless REST API, JWT validation, BigQuery client | Free tier |
| **Database** | BigQuery | Medallion architecture — Bronze, Silver, Gold datasets | Free tier |
| **Data Transforms** | Dataform (inside BigQuery) | SQL-based Bronze→Silver→Gold pipeline, Git-backed | Free |
| **Reporting** | Looker Studio Free | Executive and leader dashboards, BigQuery connector | Free |
| **Source Control** | GitHub | Monorepo: frontend + backend + infra + Dataform SQL | Free |
| **CI/CD** | GitHub Actions | Automated build, test, quality gate, and deploy | Free (2K min/mo) |
| **Code Quality** | SonarCloud | SAST, code smells, security scan on every PR | Free (public repo) |
| **Testing Automation** | TestSprite | LLM-based autonomous test generation and execution | Included (via MCP) |
| **Data Integrity Testing** | Dataform Assertions | SQL-based automated assertions executed during CI/CD and routine loads | Free |
| **Infrastructure as Code** | Terraform OSS | All GCP resources defined, versioned, and deployed as code | Free (OSS) |
| **IDE** | Google AntiGravity | Agentic AI IDE for full-stack system development ([AGENTS.md](AGENTS.md)) | Included |
| **Container Registry** | Artifact Registry | Docker image storage for Cloud Run backend | Free (≤ 0.5 GB) |
| **Secrets** | Secret Manager | API keys and credentials — never in code or env vars | Free (≤ 6 secrets) |


## 3. Person Lifecycle & Journey Stages

→ Full specification: [docs/JOURNEY_STAGES.md](docs/JOURNEY_STAGES.md)

Four admin-managed stages. Never auto-computed. Each stage is additive — it requires all fields from the previous stage plus new ones.

```plaintext
CONTACT → MEMBER → VG INTERN → VG LEADER
```

| Stage | Entry Trigger | Key Rule |
| :--- | :--- | :--- |
| **Contact** | Event registration or admin entry | Minimal fields. No One2One yet. Google account optional. |
| **Member** | Admin records One2One completion | Requires employment info + VG Leader name. Self-service via `/profile.html`. |
| **Intern** | Admin sets stage + Leader names intern in form (either first) + Admin approves relationship | `intern_relationships` record must be approved before relational link is active. |
| **Leader** | 5-step admin process (form → approve → atomic promote → close intern relationship) | Steps 3 & 4 are a single atomic API action. Step 5 has an inline prompt. |

**Field summary:**

| Field | Contact | Member | Intern | Leader |
| :--- | :--- | :--- | :--- | :--- |
| Name, Address, Contact, Birthday | ✅ | ✅ | ✅ | ✅ |
| Facebook Profile | ○ encouraged | ✅ | ✅ | ✅ |
| Employment Info | — | ✅ | ✅ | ✅ |
| VG Leader Name | — | ✅ | ✅ | ✅ |
| Groups Led + Member Names | — | — | — | ✅ |


## 4. Equipping Pathway

→ Full specification: [docs/JOURNEY_STAGES.md](docs/JOURNEY_STAGES.md)

Admin-managed only. Two valid pathways — both permanent. Completion logic lives in Gold views, not Silver schema.

| Pathway | Steps |
| :--- | :--- |
| **New (2025–present)** | One2One → Spiritual Foundations → Leadership 113 |
| **Old (pre-2025, still valid)** | One2One → Victory Weekend → Discipleship Class → Leadership 113 |

Old pathway completers are encouraged (not required) to add Spiritual Foundations. System flags them in admin view.


## 5. Event Taxonomy

→ Full specification: [docs/EVENTS.md](docs/EVENTS.md)

Four categories in `victory_silver.event_type_catalog`. New event types are added via a single admin `INSERT` — zero code changes.

| Category | Public Page? | Examples |
| :--- | :--- | :--- |
| `equipping` | No — admin roster only | Spiritual Foundations, Leadership 113 |
| `event` | Yes — self-registration | Date Talk, Marriage Booster, Convergence |
| `pastoral_self` | Yes — simplified form | Wedding, Child Dedication, Business Dedication |
| `pastoral_admin` | No — admin only | Funeral (is_sensitive = TRUE) |


## 6. Frontend & UX Flows

→ Full specification: [docs/UX_FLOWS.md](docs/UX_FLOWS.md)

Stack: HTML + Alpine.js + Bootstrap 5 on Cloudflare Pages. No build step.

| Page | Who | Access | Phase |
| :--- | :--- | :--- | :--- |
| `/e/[slug]` | Anyone | Google Sign-In | 1, 3 |
| `/profile.html` | VG Members | Google Sign-In | 1 |
| `/admin.html` | Admin only | Firebase Auth + admin role | 1 |
| `/events.html` | Admin only | Firebase Auth + admin role | 1 |
| `/leader.html` | VG Leaders | Google Sign-In | 2 |
| `/dashboard.html` | VG Leaders | Firebase Auth + vg_leader role | 2 |
| `/reports.html` | Executives | Firebase Auth + executive role | 4 |


## 7. Backend — Cloud Run + FastAPI

→ Full specification: [docs/API.md](docs/API.md)

Runtime: Python 3.12 / FastAPI / Cloud Run. Stateless. Scales to zero.

Key API routes — primary routes only. Full route table (30+ routes) in [docs/API.md](docs/API.md):

| Route | Role | Purpose |
| :--- | :--- | :--- |
| `POST /api/submit` | authenticated | VG Leader / Member form submission |
| `GET /api/me` | authenticated | Current user's profile |
| `GET /api/persons` | admin | Person search (`?q=<name>`, min 2 chars; excludes rejected records) |
| `POST /api/persons` | admin | Create person directly (admin "Create Profile" tool) |
| `PATCH /api/persons/{id}` | admin | SCD2 close-and-insert update |
| `POST /api/persons/{id}/promote-to-leader` | admin | Atomic role + stage promotion |
| `GET /api/events/{slug}/pre-check` | authenticated | Registration eligibility check |
| `POST /api/events/{slug}/self-register` | authenticated | Self-registration (409 if duplicate) |
| `POST /api/events` | admin | Create event (event_type_id, name, dates, venue, capacity, page_slug) |
| `PATCH /api/events/{id}` | admin | Update event status, hero image, or capacity |
| `POST /api/events/{id}/attend` | admin | Mark attendance; auto-creates registration for walk-ins |
| `PATCH /api/event-registrations/{id}` | admin | Update registration status (no_show/attended), payment fields |
| `PATCH /api/intern-relationships/{id}` | admin | Approve / reject / deactivate intern relationship |
| `PATCH /api/intern-relationships/{id}/link` | admin | Link unresolved intern to a person_id |
| `GET /api/intern-relationships` | admin | List intern relationships; used by admin queue Tabs 3 & 4 |
| `POST /api/intern-relationships` | admin | Admin creates an intern relationship directly (bypasses leader form) |
| `PATCH /api/vg-members/{id}/link` | admin | Link a VG member name record to an existing person_id |


## 8. Data Architecture

→ Full specification: [docs/DATA_PIPELINE.md](docs/DATA_PIPELINE.md)

```plaintext
Bronze (append-only raw)  →  Silver (SCD2 normalized)  →  Gold (read-only views)
     ↑                              ↑                              ↓
All writes first            Dataform hourly +              Looker Studio
(Cloud Run API)             Pub/Sub immediate              Admin Portal
                                                           Leader Dashboard
```

> **Exception — new user event registration:** Cloud Run performs one permitted direct
> `victory_silver.persons` write (minimal record, `review_status = 'pending'`) to
> resolve the `event_registrations.person_id` FK before Dataform runs. Bronze is still
> written first. Dataform reconciles the full record on the next scheduled run.
> Full specification: [docs/UX_FLOWS_PHASE1.md — Scenario 1](docs/UX_FLOWS_PHASE1.md).

**BigQuery datasets:** `victory_bronze` · `victory_silver` · `victory_gold`
**Trigger:** Dataform native `workflow_config` (hourly, Asia/Manila) + Cloud Function for near-real-time attendance.


## 9. Security

→ Full specification: [docs/SECURITY.md](docs/SECURITY.md)

| Layer | Technology | Protects Against |
| :--- | :--- | :--- |
| 1 — Edge | Cloudflare WAF | DDoS, bots, SQL injection, XSS |
| 2 — Transport | HTTPS / TLS 1.3 | MITM, interception |
| 3 — Auth | Firebase Auth (Google Sign-In only) | Credential attacks — no passwords |
| 4 — Authorization | FastAPI RBAC (victory_silver.person_roles) | Privilege escalation |
| 5 — Data | BigQuery Row Access Policies | Cross-persona data leakage |
| 6 — Secrets | Google Secret Manager | Credential exposure |
| 7 — Code | SonarCloud SAST | Vulnerable dependencies |


## 10. CI/CD & DevOps

→ Full specification: [docs/DEVOPS.md](docs/DEVOPS.md)

| Trigger | Pipeline |
| :--- | :--- |
| Push to `main` (frontend) | Sync `/frontend` → Cloudflare Pages |
| Push to `main` (backend) | Build Docker → push `:latest` → deploy Cloud Run |
| Push to `main` (Dataform) | Compile + run assertions (schedule handled by Dataform native) |
| Pull request | `terraform plan` + SonarCloud quality gate |
| Merge to `main` | `terraform apply` |

**SonarCloud quality gate:** Coverage > 80% · Duplication < 3% · Security Hotspots: 0 · Maintainability: A


## 11. Schema Reference

→ Full specification: [docs/SCHEMA.md](docs/SCHEMA.md)

| Dataset | Table | Type |
| :--- | :--- | :--- |
| `victory_bronze` | `raw_form_submissions` | Append-only |
| `victory_bronze` | `raw_event_actions` | Append-only |
| `victory_bronze` | `raw_headcounts` | Append-only |
| `victory_silver` | `persons` | SCD2 |
| `victory_silver` | `person_contacts` · `person_occupations` | SCD2 |
| `victory_silver` | `victory_groups` | SCD2 |
| `victory_silver` | `person_roles` · `event_type_catalog` · `equipping_classes` | Admin-managed |
| `victory_silver` | `events` · `event_registrations` · `event_attendances` · `headcounts` | Mixed |
| `victory_silver` | `equipping_enrollments` · `victory_group_members` | Mixed |
| `victory_silver` | `intern_relationships` · `ministry_catalog` · `ministry_memberships` | Admin-managed |
| `victory_silver` | `data_change_log` | Audit |
| `victory_silver` | `person_relationships` | Phase 2 |
| `victory_gold` | All `vw_*` views (14 total) | Read-only SQL views |


## 12. Reporting

→ Full specification: [docs/REPORTING.md](docs/REPORTING.md)

14 Gold views. All views joining `victory_silver.persons` must filter `WHERE persons.review_status != 'rejected'` — enforced via Dataform assertions.

Looker Studio connects via BigQuery native connector. `vw_leader_dashboard` requires "Viewer's credentials" mode for per-leader row filtering via `SESSION_USER()`.


## 13. Implementation Phases

| Phase | Focus | Scope |
| :--- | :--- | :--- |
| **Phase 1** | Foundations & Core CRM + Event Registration | Monorepo, Cloud Run, BigQuery Bronze/Silver/Gold, Dataform, Member Profile (`/profile.html`), Admin Review Queue, Google Sign-In, RBAC, Event Landing Pages, Self-registration, Duplicate checking, Admin Event Management UI, Attendance tracking. |
| **Phase 2** | VG Leader Operations | VG Leader Form (`/leader.html`), Leader Dashboard (`/dashboard.html`), Group & member lifecycle, Intern relationship management, Equipping class roster, Enrollment logic, Discipleship milestones. |
| **Phase 3** | Pastoral Events | Pastoral event self-registration (Weddings, Child Dedications, Business Dedications). |
| **Phase 4** | Executive Reporting | Looker Studio executive dashboards (`/reports`), Looker Studio drill-downs. |
| **Phase 5** | Automation & Engagement | **Person merging logic**, Audit logging, Advanced engagement scoring, Performance tuning, Extended `/profile` (badge collection, event history timeline, ministry involvement, pathway progress). |


## 14. Naming Conventions

→ Full specification (binding): [docs/NAMING.md](docs/NAMING.md)

Key rules at a glance:

| Element | Convention |
| :--- | :--- |
| BigQuery datasets | `victory_bronze` · `victory_silver` · `victory_gold` — fixed, never rename |
| Bronze tables | `raw_<entity_plural>` |
| Silver tables | `<entity_plural>` (plain plural nouns) |
| Silver SQLX files | `stg_<entity>.sqlx` |
| Gold views | `vw_<business_domain>` |
| SQL columns | `lower_snake_case` |
| API routes | `/api/<noun-plural>` in kebab-case |
| Python | `lower_snake_case` functions · `PascalCase` classes |
| Frontend files | `kebab-case.html` / `.css` / `.js` |
| Commits | `feat(scope): description` (Conventional Commits) |


## 15. Decision Log

→ Full log: [docs/DECISIONS.md](docs/DECISIONS.md)

All architectural decisions are documented in the decision log. Any deviation from this architecture requires a new entry there and an `@architect` review.

**v4.5 decisions (2026-02-24):**
- Facebook Profile encouraged at Contact, required at Member
- `intern_person_id` made nullable; raw name capture added; auto-match + admin link queue
- Duplicate resolution: Phase 1 keep-one approach; Phase 4 full merge
- VG Leader promotion: atomic Steps 3 & 4 via `POST /api/persons/{id}/promote-to-leader`
- Gold views: binding `review_status != 'rejected'` filter on all `victory_silver.persons` joins
- Admin Review Queue restructured into 4 tabs
- `stg_intern_relationships` skips insert when active approved relationship already exists
- Queue routing: pending + duplicate records → Tab 2 only until duplicate is resolved
- `POST /api/events/{slug}/self-register` accepts optional profile payload for new/incomplete users

**v4.6 decisions (2026-02-24):**
- `event_registrations.status` (`attended`/`no_show`) — manual admin PATCH only; Dataform never writes it
- `stg_vg_members.sqlx` + `stg_victory_groups.sqlx` — reconcile (replace) behavior; latest form = source of truth
- Admin Review Queue expanded to 5 tabs — Tab 5: Unlinked VG Members (`person_id IS NULL`)
- Ministry memberships — admin-only, Phase 1; no self-service path
- Event capacity — informational only in Phase 1; no registration blocking
- Account-claiming — email-match fallback on first Google Sign-In; direct `google_uid` UPDATE (not SCD2)
- `GET /api/persons` excludes `review_status = 'rejected'` records
- `data_change_log` — Cloud Run only; Dataform never writes to it
- Event status — all transitions manual admin; cancellation does not auto-cancel registrations
- Pastoral self-register — registrant ≠ celebrant; celebrant captured as `source = 'pastoral_event'` Contact record

---

*Victory Church · Master Architecture Plan · v4.6 · Confidential — Internal Use Only*
