# Victory Church — Master Architecture Plan

**Version:** 4.3 (BA Walkthrough — Process Gaps Resolved & Amendments Applied)
**Classification:** Confidential — Internal Use Only
**Scope:** Full-Stack System Design — Frontend, Backend, Data, DevOps, Security, Business Logic & UX


## Table of Contents

- [Architecture Overview](#1-architecture-overview)
- [Technology Stack Summary](#2-technology-stack-summary)
- [Person Lifecycle & Journey Stages](#3-person-lifecycle--journey-stages)
- [Equipping Pathway](#4-equipping-pathway)
- [Event Taxonomy](#5-event-taxonomy)
- [Frontend — Cloudflare Pages](#6-frontend--cloudflare-pages)
- [Backend — Cloud Run + FastAPI](#7-backend--cloud-run--fastapi)
- [Data Architecture — Bronze → Silver → Gold](#8-data-architecture--bronze--silver--gold)
- [Data Flow Diagram](#9-data-flow-diagram)
- [CI/CD Pipeline — GitHub Actions + Terraform](#10-cicd-pipeline--github-actions--terraform)
- [Security Architecture](#11-security-architecture)
- [UX Flows](#12-ux-flows)
- [Schema Reference — All Tables](#13-schema-reference--all-tables)
- [Gold Views — Reporting Layer](#14-gold-views--reporting-layer)
- [Development IDE — Google AntiGravity](#15-development-ide--google-antigravity)
- [Component Compatibility Matrix](#16-component-compatibility-matrix)
- [Implementation Phases](#17-implementation-phases)
- [Decision Log](#18-decision-log)
- [Naming Conventions & Consistency Standards](#19-naming-conventions--consistency-standards)


## 1. Architecture Overview

Victory Church's member and ministry management system is a full-stack, cloud-native application built entirely on free-tier eligible, production-grade services. It manages the full lifecycle of members — from first contact through equipping, intern, and leadership stages — plus event management, equipping pathway tracking, and executive reporting.

### Design Principles

- **Free-tier first.** Every component runs within free-tier limits at current scale.
- **Bronze → Silver → Gold medallion architecture.** Raw data is never mutated. Transformations are versioned SQL.
- **Admin-managed, never auto-computed.** Journey stage, role assignment, and pathway completion are pastoral judgments — the system informs but never replaces human decision-making.
- **Additive schema changes only.** No existing data is ever deleted or migrated destructively.
- **Stateless backend.** Cloud Run scales to zero; all session state is in Firebase Auth JWTs.
- **Completion logic lives in Gold views.** When business rules change, only SQL views are updated — no Silver schema migration required.
- **Duplicate-safe event registration.** The system prevents duplicate event registrations at the API layer and informs returning registrants of their existing status.
- **Data sovereignty.** All data resides strictly within GCP Philippines/Taiwan regions. No member data is processed or stored by external SaaS providers (Cloudflare handles only edge traffic — no member PII passes through it).


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
| **Container Registry** | Artifact Registry | Docker image storage for Cloud Run backend | Free (≤ 0.5 GB — enforced by `:latest`-only cleanup policy in Terraform) |
| **Secrets** | Secret Manager | API keys and credentials — never in code or env vars | Free (≤ 6 secrets) |

## 3. Person Lifecycle & Journey Stages

`journey_stage` is a single admin-managed field on `silver.persons`. It is never auto-computed or inferred from other fields. This preserves pastoral judgment — only a leader who knows the person can accurately assess their stage.

### The Four Stages

Copy
```plaintext
CONTACT → MEMBER → VG INTERN → VG LEADER
```

Each stage has required information that must be collected and maintained. Fields are additive — each stage requires everything from the previous stage plus new fields.

### Stage 01 — Contact

- **Definition:** In the system, not yet a member.
- **Entry point:** Registered for an event, or admin entered them during data migration or a pastoral event.
- **Characteristics:** Has not completed One2One. May have no Google account linked yet.
- **Next step:** Encourage One2One → becomes a Member.

**Required fields:**

| Field | Storage Location | Notes |
| :--- | :--- | :--- |
| First Name | silver.persons.first_name | |
| Middle Name | silver.persons.middle_name | Common in PH (mother's maiden name) |
| Last Name | silver.persons.last_name | |
| Suffix | silver.persons.suffix | Jr., Sr., III, etc. — None if not applicable |
| Address | silver.persons.address | Full address, single text field |
| Contact Number | silver.person_contacts (type: mobile) | |
| Birthday | silver.persons.birthdate | |
| Facebook Profile | silver.person_contacts (type: facebook) | URL or profile name — **encouraged at Contact stage, required from Member stage onward** |

### Stage 02 — Member

- **Definition:** Completed One2One, part of the movement. Consumer stage.
- **Entry point:** Admin records `one2one_completed = true` and `one2one_date`. Sets `journey_stage = member`.
- **Characteristics:** Part of a Victory Group as a member. Attends events and services.
- **Self-service data collection:** VG Members submit their employment info and VG Leader name via `/profile.html` (Google Sign-In). The form pre-fills from their existing Silver record and writes to `bronze.raw_form_submissions`. Dataform reconciles on the next scheduled run. Admin may also enter this data directly via the admin portal.
- **Admin portal soft-warning:** When admin sets `journey_stage = member`, the portal checks whether `vg_leader_first_name` and `vg_leader_last_name` are populated. If either is missing, a soft warning is displayed: *"VG Leader name is missing for this member. Please collect and enter it."* This does **not** block the stage transition — admin may proceed — but the warning ensures the gap is visible. The record will appear with a low `profile_completeness_pct` in admin views until resolved.
- **Next step:** Become a VG Intern while progressing through the Equipping Pathway.

**Required fields (all Contact fields plus):**

| Field | Storage Location | Notes |
| :--- | :--- | :--- |
| Employment Type | silver.person_occupations.employment_type | employed or self_employed |
| If employed: Nature of Work | silver.person_occupations.nature_of_work | e.g. Accounting, Engineering, Teaching |
| If employed: Company Name | silver.person_occupations.company_name | |
| If self-employed: Nature of Business / Freelance Industry | silver.person_occupations.nature_of_business | e.g. Food, Retail, Graphic Design |
| If self-employed: Business Name | silver.person_occupations.business_name | |
| VG Leader First Name | silver.persons.vg_leader_first_name | Name of their Victory Group leader |
| VG Leader Last Name | silver.persons.vg_leader_last_name | |

### Stage 03 — VG Intern

- **Definition:** Being discipled, training to lead.
- **Entry point — two steps, both required:**
  1. **Admin** sets `journey_stage = intern` on the person's record in the admin portal.
  2. **VG Leader** identifies the intern on the VG Leader form (Section 3 — Interns I'm Supervising). This creates a `pending` `intern_relationships` record. Admin reviews and confirms in the admin portal, which activates the relational link (`review_status = 'approved'`, `is_active = TRUE`).
- **Sequencing:** Either step may happen first, but the `intern_relationships` record is not considered active until admin confirms it. The Silver pipeline only syncs `vg_leader_first_name/last_name` from an `approved` relationship.
- **Characteristics:** Active intern under a VG Leader. Listed in `silver.intern_relationships` linked to their supervising leader (after admin confirmation).
- **Admin queue alert — unlinked interns:** The admin portal surfaces a dedicated alert queue for persons where `journey_stage = 'intern'` but no `intern_relationships` record with `review_status = 'approved'` and `is_active = TRUE` exists. These are interns who have been stage-promoted but whose relational link is pending, unresolved, or missing. Admin is prompted to either approve a pending relationship or create one directly via `POST /api/intern-relationships`.
- **Next step:** Lead their own group → becomes a VG Leader.

**Required fields:** Same as Member. The intern is still under a VG Leader and has the same data requirements.

**Leader linkage — two layers:**
- `vg_leader_first_name` / `vg_leader_last_name` on `silver.persons` — display cache. Pre-populated when the person was at member stage and may reference a leader not yet in the system. Present at all stages.
- `silver.intern_relationships.leader_person_id` — canonical FK for the intern-leader data relationship. Requires the supervising leader to be a registered `silver.persons` record. `review_status = 'approved'` indicates the admin has confirmed the relationship. This is the authoritative relational link for interns.
- The Silver pipeline (`stg_persons.sqlx`) derives and keeps `vg_leader_first_name/last_name` in sync from the linked leader's `first_name`/`last_name` when a valid `leader_person_id` exists in `intern_relationships` with `review_status = 'approved'`.
- If multiple active approved relationships exist for the same intern (edge case), the pipeline uses the most recent `start_date`.

### Stage 04 — VG Leader

- **Definition:** Leading their own Victory Group(s).
- **Entry point — five sequential admin actions (all required):**
  1. Person submits VG Leader form (`/leader.html`). Admin must wait until after the next Dataform run (up to 1 hour) for the leader's victory groups to appear in `silver.victory_groups` before proceeding to Step 2.
  2. Admin reviews the submission in the admin portal (approves the person record — `review_status = 'approved'`).
  3. **Admin executes Steps 3 and 4 as a single atomic UI action:** The admin portal exposes a single **"Promote to VG Leader"** button on the person's record view. This button simultaneously (a) INSERTs the `vg_leader` role into `silver.person_roles` and (b) SCD2 PATCHes `journey_stage = 'leader'` on `silver.persons` in a single API call (`POST /api/persons/{id}/promote-to-leader`). The two operations are never performed as separate actions — splitting them creates a data inconsistency state (`vg_leader` role without `journey_stage = 'leader'`, or vice versa). The admin portal must not expose separate controls for these two fields on a person already being promoted. A person with mismatched role and stage (e.g., from a prior incomplete action) is surfaced as a **data inconsistency warning** in the person's record view with a prompt to resolve.
  4. *(Included in Step 3 atomic action — see above.)*
  5. **Admin closes the person's active intern relationship** (if they were previously a VG Intern). Immediately after the "Promote to VG Leader" action completes, the admin portal checks for any active `intern_relationships` records (`is_active = TRUE`) for this person. If found, an **inline prompt** is displayed: *"This person has an active intern relationship with [Leader Name]. Close it now?"* with a **[ Close Relationship ]** button that calls `PATCH /api/intern-relationships/{id}` with `is_active = FALSE` and `end_date = today`. Admin must explicitly act — the system does not auto-close. If dismissed, the portal re-surfaces the open relationship as a warning on the person's record view until resolved. Without this step, the former intern remains in active intern counts and in their supervising leader's form pre-fill indefinitely.
- **Characteristics:** Has at least one active group in `silver.victory_groups`. Fills in the VG Leader form. Has the `vg_leader` role in `silver.person_roles`.
- **Encouraged to:** Complete Equipping Pathway if not already done. Go back for Spiritual Foundations if on old pathway.

**Required fields (all Member/Intern fields plus):**

| Field | Storage Location | Notes |
| :--- | :--- | :--- |
| Groups Led (count) | | Derived from silver.victory_groups: COUNT of active groups where leader_person_id = this person |
| Type of Each Group | silver.victory_groups.group_type | single · wives · husbands · students · young_pro |
| Members of Each Group | silver.victory_group_members | First name + last name per member per group |

Note: The VG Leader form captures group and member information directly. The number of groups led is not a stored field — it is derived from the count of active silver.victory_groups records for that leader. Group types and member rosters are entered per group.


### Field Summary by Stage

| Field | Contact | Member | Intern | Leader |
| :--- | :--- | :--- | :--- | :--- |
| First Name, Middle Name, Last Name, Suffix | ✅ | ✅ | ✅ | ✅ |
| Address | ✅ | ✅ | ✅ | ✅ |
| Contact Number | ✅ | ✅ | ✅ | ✅ |
| Birthday | ✅ | ✅ | ✅ | ✅ |
| Facebook Profile | ○ encouraged | ✅ | ✅ | ✅ |
| Employment Info | — | ✅ | ✅ | ✅ |
| VG Leader Name | — | ✅ | ✅ | ✅ |
| Groups Led + Types | — | — | — | ✅ |
| VG Member Names | — | — | — | ✅ |

### Core Fields on `silver.persons`

| Field | Type | Values / Notes |
| :--- | :--- | :--- |
| `first_name` | STRING | Required. |
| `middle_name` | STRING | Required in PH context (mother's maiden name). |
| `last_name` | STRING | Required. |
| `suffix` | STRING | Jr., Sr., III, etc. NULL if not applicable. |
| `full_name` | STRING | Computed by Silver pipeline: first_name middle_name last_name suffix. |
| `address` | STRING | Full address, single text field. |
| `is_in_victory_group` | BOOL | Captured during event registration. NULL = not yet answered. |
| `vg_leader_first_name` | STRING | First name of their VG Leader. Set at member/intern stage. |
| `vg_leader_last_name` | STRING | Last name of their VG Leader. Set at member/intern stage. |
| `journey_stage` | STRING | contact · member · intern · leader — admin-set. Default: contact. |
| `one2one_completed` | BOOL | Set to TRUE by admin when personal meeting is confirmed. |
| `one2one_date` | DATE | Date the One2One meeting occurred. NULL until completed. |
| `google_uid` | STRING | Firebase Auth UID. NULL for migrated/admin-created records until first sign-in. |
| `review_status` | STRING | pending · approved · rejected. All new submissions start as pending. |
| `source` | STRING | form_submission · event_registration · admin_created · pastoral_event |
| `duplicate_flag` | BOOL | Set by pipeline when name + birthday match found across different google_uid records. |
| `duplicate_of_person_id` | STRING FK | Points to the likely canonical record. Admin resolves. |
| `profile_completeness_pct` | INT64 | 0–100. Computed by Silver pipeline based on stage-appropriate required fields. |

## 4. Equipping Pathway

Admin-managed, not self-reported. VG Leaders and Members are never asked what they've completed — the admin records it. The pathway has two valid versions (old and new). Both are permanently valid.

### New Pathway (2025–present)

| Step | Name | Canonical Key | Tracking Method |
| :--- | :--- | :--- | :--- |
| 1 | One2One | `one2one` | Fields on `silver.persons` — not a class record |
| 2 | Spiritual Foundations | `spiritual_foundations` | `silver.equipping_classes` + roster |
| 3 | Leadership 113 | `leadership_113` | `silver.equipping_classes` + roster |

### Old Pathway (pre-2025, still valid)

| Step | Name | Canonical Key | Tracking Method |
| :--- | :--- | :--- | :--- |
| 1 | One2One | `one2one` | Fields on `silver.persons` — not a class record |
| 2 | Victory Weekend | `victory_weekend` | `silver.equipping_classes` + roster |
| 3 | Discipleship Class (aka Leader's Lab) | `discipleship_class` | `silver.equipping_classes` + roster. `step_name_as_completed` preserves original name. |
| 4 | Leadership 113 | `leadership_113` | `silver.equipping_classes` + roster |

Note on Leader's Lab: Leader's Lab was a temporary rename of Discipleship Class. Any record where step_name_as_completed = "Leader's Lab" maps to canonical_step = discipleship_class. This is handled in the Silver pipeline — historically accurate, reports correctly.

### Canonical Step Name Mapping

| Canonical Step | Historical Names | Pathway | How Tracked |
| :--- | :--- | :--- | :--- |
| `one2one` | One2One | Both | Fields on `silver.persons` — not a class record |
| `victory_weekend` | Victory Weekend | Old only | `silver.equipping_classes` + roster |
| `discipleship_class` | Discipleship Class, Leader's Lab | Old only | `silver.equipping_classes` + roster — `step_name_as_completed` preserves original names |
| `spiritual_foundations` | Spiritual Foundations | New (encouraged for old) | `silver.equipping_classes` + roster |
| `leadership_113` | Leadership 113 | Both | `silver.equipping_classes` + roster |
### Pathway Completion Rules (Gold View Logic)

Completion logic lives in Gold views, not the Silver schema. When the pathway changes again, only `gold.vw_equipping_completion` needs updating — no Silver schema changes, no data migration, no historical records touched.

| Completion Type | Definition | Action Surfaced |
| :--- | :--- | :--- |
| New pathway complete | Has `one2one` + `spiritual_foundations` + `leadership_113` | Fully equipped badge on person profile |
| Old pathway complete | Has `one2one` + `discipleship_class` + `leadership_113` | Fully equipped badge on person profile. Encouraged: add SF. |
| Old pathway complete but missing SF | Flag in admin view: "Encourage Spiritual Foundations" | |
| Ready for next step | Has Step N completed but not Step N+1 for their pathway | Listed in "Pathway Pipeline" drill-down per step |
| Victory Weekend legacy | Has `victory_weekend` | Shown in old pathway funnel, not new pathway funnel |

## 5. Event Taxonomy

Four distinct categories in `silver.event_type_catalog`. Adding a new event type is always a single admin `INSERT` — zero code changes.

### Category Definitions

#### 🎓 Equipping Pathway

- **Examples:** Victory Weekend, Spiritual Foundations, Discipleship Class, Leadership 113
- **Registration:** Admin-managed class roster only. No public landing page. No self-registration.
- **Data entry:** Admin creates class batch, manages enrolled → completed / dropped.
- **Profile impact:** Completion updates `silver.equipping_enrollments`. Gold views compute pathway progress.
- **Attendance tracking:** Per-class roster with start/end date. Batch cohort identity preserved.

#### 🎉 Events

- **Examples:** Date Talk, Marriage Booster, Convergence, Family Day
- **Registration:** Public self-registration via standalone event landing page (`/e/[slug]`). Canva-designed hero image uploaded by admin. Registration form includes "Are you part of a Victory Group?" question for new registrants.
- **Data entry:** Person self-registers. Admin confirms payment for paid events.
- **Profile impact:** Attendance record only. No milestone update. Contributes to engagement score (frequency, recency, variety).
- **Lead gen:** New registrants without a profile are redirected to complete their profile before registration is confirmed.
- **Duplicate protection:** System checks for existing registration before allowing submission and informs the person if already registered.

#### ⛪ Pastoral Events (self-register)

- **Examples:** Wedding, Child Dedication, Property Dedication, Business Dedication
- **Registration:** Family/couple registers via a dedicated pastoral event page with a simplified form.
- **Data entry:** Self-registered by the family OR admin-entered, depending on event type.
- **Profile impact:** Person being celebrated is created as a new contact record if no existing match. Source tagged as `pastoral_event`.
- **Lead gen:** A Wedding registration creates two new contact records (the couple) if they don't exist. Admin follows up to encourage One2One.

#### 🕊️ Pastoral Events (admin-only)

- **Examples:** Funeral / Necrological Service
- **Registration:** No public page. Admin always enters these directly.
- **Data entry:** Admin creates event, adds family members the pastoral team wants to follow up with as new contact records.
- **Profile impact:** New contacts created with source = `pastoral_event`. Flagged in admin queue for pastoral follow-up.
- **Sensitivity:** Funeral records flagged as `is_sensitive = TRUE` — limits visibility to admin and pastoral staff only. Excluded from all executive views.

#### `silver.event_type_catalog` Category Values

| category value | Label | `equipping_step` field | Public page? |
| :--- | :--- | :--- | :--- |
| `equipping` | Equipping Pathway | Set (e.g. `spiritual_foundations`) | No — admin roster only |
| `event` | Events | NULL | Yes — Canva hero + self-registration |
| `pastoral_self` | Pastoral (self-register) | NULL | Yes — dedicated pastoral form |
| `pastoral_admin` | Pastoral (admin-only) | NULL | No — admin portal only |
| `outreach` | Outreach / Mission | NULL | Optional — future |
| `worship` | Worship / Prayer Night | NULL | Optional — future |
| `youth` | Youth Events | NULL | Optional — future |
| `fellowship` | Fellowship / Social | NULL | Optional — future |

## 6. Frontend — Cloudflare Pages

Host: Cloudflare Pages | Stack: HTML + Alpine.js + Bootstrap 5

The existing HTML/CSS/JavaScript stack is 100% compatible with Cloudflare Pages — no migration or rewrite needed.

### Why Cloudflare Pages

| Option | Free Tier | CDN | Deploy from GitHub | Custom Domain | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cloudflare Pages** | Unlimited bandwidth | Yes — 200+ PoPs | Yes — automatic | Yes + auto HTTPS | **Recommended** |
| **GitHub Pages** | Unlimited (public only) | Limited | Yes | Yes | Limited — no WAF integration |
| **Netlify** | 100 GB bandwidth/mo | Yes | Yes | Yes | Good — but bandwidth cap |
| **Vercel** | 100 GB bandwidth/mo | Yes | Yes | Yes | Good — but bandwidth cap |
| **Firebase Hosting** | 10 GB/mo | Yes | Via Actions | Yes | Lower limits |
### Cloudflare Pages Setup

Copy
```plaintext
GitHub repo → (OAuth) → Cloudflare Pages
  - Build command: none (plain HTML — just /frontend directory)
  - Push to main → auto production deploy in ~30 seconds
  - Pull request → unique preview URL (e.g. pr-12.victory-church.pages.dev)
  - Custom domain (members.victorychurch.ph) → Cloudflare DNS → HTTPS automatic
```
### Page Structure

| Page | Who Sees It | Access Control | Notes |
| :--- | :--- | :--- | :--- |
| `/` (form) | VG Leaders | Cloudflare Access redirect to Google login | Existing page — no changes needed |
| `/admin.html` | Admin only | Firebase Auth + role check (admin) | Admin UI for editing data and managing events |
| `/events.html` | Admin only | Firebase Auth + role check (admin) | Event management: create, register, mark attendance |
| `/dashboard.html` | Leaders | Firebase Auth + role check (`vg_leader`) | Personal group and discipleship overview |
| `/reports.html` | Executives | Looker Studio embed or direct link | Embedded Looker Studio reports or direct share link |
| `/e/[slug]` | Anyone | Google Sign-In | Public event landing page — no nav |
| `/leader.html` | VG Leaders | Google Sign-In | VG Leader form — pre-fills for returning users |
| `/profile.html` | VG Members | Google Sign-In | Phase 1: own record view and edit. Pre-fills from existing Silver record. Collects member-stage fields (employment type + conditional fields, VG Leader name) that the VG Leader form does not cover. Cannot see other records. |
### Mobile Responsiveness Strategy

- Bootstrap 5 grid provides mobile-first responsiveness for the existing member form.
- Build with Bootstrap breakpoints: `xs` (320px+), `sm` (576px+), `md` (768px+), `lg` (992px+).
- Test on real devices using Google AntiGravity's preview capabilities or BrowserStack free tier.
- Touch targets: minimum 44×44px for all interactive elements per WCAG 2.1.
- Font sizes: minimum 16px body text to prevent iOS auto-zoom on form fields.
- Viewport meta tag enforced: `width=device-width, initial-scale=1.0`.

### Event Page Design

Copy
```plaintext
Admin's job                          Creative team's job
─────────────────────────────────    ──────────────────────────────────
Create event in portal               Design event artwork in Canva
System auto-generates page_slug      Export as image, send to admin
Upload Canva-designed hero image     Admin uploads it — page is live
Set status = registration_open       Creative team never touches code
Copy URL → hand to comms team        Zero developer required
```
### Event Landing Page Layout (`/e/[slug]`)

Copy
```plaintext
┌─────────────────────────────────────────┐
│         [Canva Hero Image]              │
│                                         │
│  Event Name                             │
│  Date & Time · Venue                    │
│  Description (optional)                 │
│                                         │
│  ┌─────────────────────────────┐        │
│  │   [ Register Now ]          │        │
│  └─────────────────────────────┘        │
│                                         │
│  No payment instructions displayed.     │
│  No site navigation.                    │
└─────────────────────────────────────────┘
```

## 7. Backend — Cloud Run + FastAPI

Runtime: Python 3.12 | Framework: FastAPI | Host: Google Cloud Run

Cloud Run hosts a containerized Python FastAPI application. It scales automatically from zero — when no one is using the app, it costs nothing.

### Why FastAPI on Cloud Run

- **FastAPI:** Automatic request validation (Pydantic), async support, built-in OpenAPI/Swagger docs.
- **Cloud Run:** Scales to zero (free when idle), 2M requests free/month, no server management, Docker-native.
- **Python:** Huge library ecosystem for Google Cloud (`google-cloud-bigquery`, `firebase-admin`).
- **Stateless:** Each request is independent — no session state on the server.

### API Route Structure

| Route Group | Methods | Allowed Roles | Description |
| :--- | :--- | :--- | :--- |
| `POST /api/submit` | POST | `vg_leader` | VG Leader form submission — writes to bronze |
| `GET /api/me` | GET | authenticated | Returns current user's profile by `google_uid` |
| `GET /api/persons` | GET | admin | List persons. Supports `?q=<name>` for name search (used in VG member linking and intern search). Returns matching `silver.persons` records (`is_current = TRUE`) ordered by relevance. Minimum query length: 2 characters. |
| `PATCH /api/persons/{id}` | PATCH | admin | Update a person record. Must implement SCD2 close-and-insert — see Write-Path Ownership Matrix. |
| `POST /api/persons/{id}/promote-to-leader` | POST | admin | Atomic promotion to VG Leader. Simultaneously (1) INSERTs `vg_leader` role into `silver.person_roles` and (2) SCD2 PATCHes `journey_stage = 'leader'` on `silver.persons`. Both operations succeed or both fail — no partial state. Returns the updated person record and a flag `has_active_intern_relationship` so the frontend can surface the Step 5 inline prompt. |
| `GET /api/events` | GET | admin, executive | List all events |
| `POST /api/events` | POST | admin | Create new event instance |
| `GET /api/events/{slug}/pre-check` | GET | authenticated | Pre-registration check: person exists, profile completeness, duplicate registration check, upcoming event list |
| `POST /api/events/{slug}/self-register` | POST | authenticated | Self-register for a public event. Returns 409 if already registered. |
| `POST /api/events/{id}/register` | POST | admin | Admin registers a person for an event |
| `POST /api/events/{id}/attend` | POST | admin | Mark attendance. If no prior registration exists (walk-in), auto-creates a `registered` registration record with `payment_status = 'pending'` (paid events) or `'N/A'` (free events) before writing the attendance. Triggers discipleship pipeline. |
| `POST /api/headcounts` | POST | admin | Submit anonymous headcount for an event or Sunday Service |
| `GET /api/leaders/me` | GET | `vg_leader` | VG Leader's own profile, groups, and member list |
| `PATCH /api/vg-members/{id}/link` | PATCH | admin | Link a VG member name record to an existing `person_id` |
| `GET /api/intern-relationships` | GET | admin | List intern relationship records. Supports `?status=pending` filter for admin review queue. Returns `intern_person_id`, `leader_person_id`, `review_status`, `is_active`, `source`, `start_date`. |
| `POST /api/intern-relationships` | POST | admin | Create an intern relationship directly (admin-initiated, bypasses leader form). `review_status` defaults to `approved` for admin-created records. `source = 'admin_created'`. |
| `PATCH /api/intern-relationships/{id}` | PATCH | admin | Approve, reject, or deactivate an intern relationship. Permitted field updates: `review_status` (`approved` / `rejected`), `is_active` (`FALSE` to close), `end_date`. Used for both admin review of leader-form submissions and closing relationships when an intern is promoted to VG Leader. |
| `PATCH /api/intern-relationships/{id}/link` | PATCH | admin | Link an unresolved intern relationship to an existing `silver.persons` record. Body: `{ "intern_person_id": "<uuid>" }`. Required before an `intern_relationships` record with `intern_person_id = NULL` can be approved. |
| `GET /api/health` | GET | public | Health check endpoint (for Cloud Run uptime) |
### Authentication Flow

Copy
```plaintext
1. User opens app → Firebase Auth SDK prompts Google Sign-In if not authenticated
2. Firebase returns a signed JWT ID token (valid 1 hour, auto-refreshed)
3. Frontend includes JWT as Authorization: Bearer <token> on every API call
4. Cloud Run FastAPI middleware calls Firebase Admin SDK to verify JWT signature
5. If valid: extract email → look up role in silver.person_roles → attach to request context
6. Route-level decorators check required role → allow or return 403 Forbidden
```
### Pre-Registration Check (`GET /api/events/{slug}/pre-check`)

This endpoint is the backbone of the smart event registration flow. Called immediately after Google Sign-In on an event landing page, it returns all the data the frontend needs to render the correct screen.
**Request:**

```plaintext
GET /api/events/date-talk-feb-2025/pre-check
Authorization: Bearer <JWT>
```
**Response — Person exists, complete profile, NOT registered:**

```json
{
  "person_found": true,
  "person_name": "Juan Dela Cruz",
  "profile_complete": true,
  "already_registered": false,
  "existing_registration": null,
  "upcoming_registrations": [
    {
      "event_name": "Marriage Booster",
      "event_date": "2025-03-01",
      "status": "registered"
    }
  ]
}
```
**Response — Person exists, ALREADY registered for this event:**

```json
{
  "person_found": true,
  "person_name": "Juan Dela Cruz",
  "profile_complete": true,
  "already_registered": true,
  "existing_registration": {
    "registration_id": "reg-abc-123",
    "status": "registered",
    "registered_at": "2025-01-20T10:00:00Z"
  },
  "upcoming_registrations": [
    {
      "event_name": "Date Talk — Feb 2025",
      "event_date": "2025-02-15",
      "status": "registered"
    },
    {
      "event_name": "Marriage Booster",
      "event_date": "2025-03-01",
      "status": "registered"
    }
  ]
}
```
**Response — Person exists, incomplete profile:**

```json
{
  "person_found": true,
  "person_name": "Juan Dela Cruz",
  "profile_complete": false,
  "profile_completeness_pct": 62,
  "missing_fields": ["address", "contact_number", "facebook_profile"],
  "already_registered": false,
  "existing_registration": null,
  "upcoming_registrations": []
}
```
**Response — Person not found (new user):**

```json
{
  "person_found": false,
  "profile_complete": false,
  "already_registered": false,
  "existing_registration": null,
  "upcoming_registrations": []
}
```
**Backend logic:**

1. Verify JWT → extract `google_uid`.
2. Query `silver.events` for the given `slug`. If not found → return 404. If `status != 'registration_open'` → return 410 Gone with `{ "event_status": "<status>", "message": "Registration is not open for this event." }`. Frontend shows an appropriate closed/cancelled screen — no registration is possible.
3. Query `silver.persons` for matching `google_uid` (WHERE `is_current = TRUE`).
4. If person found → query `silver.event_registrations` for this event + person (WHERE `status != 'cancelled'`).
5. If person found → query `silver.event_registrations` for ALL upcoming events (WHERE `event.start_datetime > NOW()` AND `status IN ('registered')`).
6. Compute `profile_complete` by checking contact-stage required fields. Fields on `silver.persons` (`first_name`, `middle_name`, `last_name`, `suffix`, `address`, `birthdate`) are checked directly. `contact_number` is resolved by LEFT JOINing `silver.person_contacts WHERE contact_type = 'mobile' AND is_current = TRUE`. `facebook_profile` is resolved by LEFT JOINing `silver.person_contacts WHERE contact_type = 'facebook' AND is_current = TRUE`. If any required field is NULL or missing, `profile_complete = false` and `missing_fields` is populated with the field names.
7. Return assembled response.

> **Known limitation:** For a new user created via the two-phase write (Section 12, Scenario 1), `profile_completeness_pct` on `silver.persons` defaults to `0` until the next Dataform run (up to 1 hour). If the same user visits a second event landing page within this window, the backend computes completeness dynamically via the JOINs above (step 6) rather than relying on `profile_completeness_pct` — ensuring the pre-check returns an accurate result. `profile_completeness_pct` is used for reporting and admin views only. It is not used by the pre-check endpoint.

### Duplicate Registration Prevention (`POST /api/events/{slug}/self-register`)

```python
# Pseudocode for self-register endpoint
def self_register(slug, jwt_user):
    person = lookup_person(jwt_user.google_uid)
    event = lookup_event(slug)

    # 0. Re-validate event status at write time (guards against race condition
    #    between pre-check and self-register calls)
    if event.status != 'registration_open':
        return 410, {
            "event_status": event.status,
            "message": "Registration is not open for this event."
        }

    # 1. Check profile completeness
    if not person.profile_complete:
        return 422, "Profile incomplete. Complete your profile first."

    # 2. Check for existing active registration
    existing = query(
        "SELECT * FROM silver.event_registrations "
        "WHERE event_id = @event_id AND person_id = @person_id "
        "AND status != 'cancelled'"
    )
    if existing:
        return 409, {
            "message": "You are already registered for this event.",
            "registration": existing
        }

    # 3. Create registration with deterministic ID for idempotency
    registration_id = sha256(f"{event.event_id}:{person.person_id}")
    insert_registration(registration_id, event.event_id, person.person_id)

    return 201, {"message": "Registration confirmed.", "registration_id": registration_id}
```

**Idempotency:** The `registration_id` is computed as a deterministic hash of `event_id` + `person_id`. This means even if the request is accidentally sent twice (double-click, network retry), the same ID is generated and BigQuery treats it as a no-op on the second insert.

### Discipleship Auto-Pipeline (Event Attendance → Enrollment Completion)

Events and equipping classes are separate systems. Equipping enrollment is exclusively admin-managed via class rosters. The discipleship pipeline does **not** create new enrollment records — it marks existing `enrolled` records as `completed` when admin confirms attendance at an equipping event session.

**Pre-condition:** Admin must enroll a person in an equipping class (via the admin class roster, setting `enrollment_status = 'enrolled'`) before marking attendance. The pipeline finds that enrollment record and updates it — if no enrolled record exists, the pipeline is a no-op for that person.

Copy
```plaintext
1. Admin pre-enrolls persons in a class via the admin class roster portal.
   silver.equipping_enrollments created with enrollment_status = 'enrolled'.

2. Admin POSTs to /api/events/{id}/attend with person_id (at the actual class session).

3. Cloud Run writes attendance to bronze.raw_event_actions (immediate, streaming insert).

4. Cloud Run publishes a Pub/Sub message. Cloud Function dataform-attendance-trigger fires.

5. Dataform stg_attendances.sqlx reads from bronze → MERGE-upserts to silver.event_attendances.

6. Dataform discipleship_pipeline.sqlx reads from:
     silver.event_attendances + silver.event_type_catalog
     + silver.equipping_enrollments + silver.equipping_classes
   → UPDATES silver.equipping_enrollments SET
       enrollment_status = 'completed',
       completed_at = checked_in_at
   WHERE person has an 'enrolled' record whose equipping_classes.canonical_step
     matches the event's event_type_catalog.equipping_step.
   Short-circuits (no-op) when equipping_step IS NULL on the event.
   If multiple enrolled records exist for the same step, the most recent (by enrolled_at) is updated.

7. Gold views update automatically — Looker Studio reflects the change on next data refresh.
```

> **Write-path rule:** Cloud Run writes attendance data to `bronze` only. `silver.event_attendances` is owned exclusively by Dataform. `silver.equipping_enrollments` is created by admin via the admin portal (enrolled status) and updated to `completed` by the Dataform pipeline after attendance is confirmed. Admin corrections to existing silver records are permitted directly via admin portal PATCH endpoints, but initial attendance records always originate from bronze via the Dataform pipeline.
>
> **Enrollment rule:** The pipeline never auto-creates enrollment records. Admin must enroll a person before attendance can trigger a completion update. This preserves the pastoral oversight principle — a person cannot be marked as completing an equipping step without deliberate admin enrollment.

### Write-Path Ownership Matrix

This table is the authoritative reference for which component is permitted to write to each Silver table and what write pattern it must follow. Deviating from this table requires an `@architect` review and a Decision Log entry.

| Silver Table | Dataform (scheduled) | Cloud Run (API) | Write Pattern |
| :--- | :--- | :--- | :--- |
| `persons` | ✅ Owns initial creation + SCD2 upsert | ✅ Exception: minimal record on new-user event registration (two-phase write). Admin PATCH: SCD2 close-and-insert. | SCD2 — every write closes the current row and inserts a new row with updated `valid_from`, `valid_to = NULL`, `is_current = TRUE`. |
| `person_contacts` | ✅ Owns initial creation + SCD2 upsert | ✅ Admin PATCH: SCD2 close-and-insert. | SCD2 |
| `person_occupations` | ✅ Owns initial creation + SCD2 upsert | ✅ Admin PATCH: SCD2 close-and-insert. | SCD2 |
| `victory_groups` | ✅ Owns initial creation + SCD2 upsert | ✅ Admin PATCH: SCD2 close-and-insert. | SCD2 |
| `victory_group_members` | ✅ Owns initial creation | ✅ Admin PATCH (link/unlink): direct UPDATE (not SCD2 — no history tracking on `person_id` link). | Direct UPDATE on `person_id` field only. |
| `person_roles` | ❌ Not managed by Dataform | ✅ Admin only: INSERT new role record. Deactivation: `is_active = FALSE` UPDATE. | INSERT for new roles; direct UPDATE for deactivation. |
| `intern_relationships` | ✅ INSERTs new `pending` records from Bronze form data | ✅ Admin only: PATCH to set `review_status = 'approved' / 'rejected'`, `is_active = FALSE`, `end_date`. | Dataform INSERTs; admin PATCHes status fields in-place (not SCD2). |
| `equipping_classes` | ❌ Not managed by Dataform | ✅ Admin only: full CRUD. | Direct INSERT/UPDATE. |
| `equipping_enrollments` | ✅ UPDATEs `enrolled → completed` via discipleship pipeline | ✅ Admin: INSERT (`enrolled` status), PATCH (status corrections). | Dataform UPDATE; admin INSERT/PATCH. |
| `events` | ✅ Creates from Bronze `action_type = 'created'` | ✅ Admin PATCH (status, capacity, hero image). | Dataform INSERT; admin PATCH in-place. |
| `event_registrations` | ✅ Creates from Bronze `action_type = 'registered'` | ✅ Cloud Run direct INSERT for two-phase write (new-user event reg). Admin PATCH (payment status). | Dataform INSERT; Cloud Run INSERT (exception); admin PATCH in-place. |
| `event_attendances` | ✅ Exclusively owns via `stg_attendances.sqlx` | ❌ No direct Cloud Run writes. Admin corrections via admin PATCH only. | Dataform MERGE-upsert; admin PATCH in-place for corrections. |
| `headcounts` | ✅ Creates from Bronze `raw_headcounts` | ❌ No direct Cloud Run writes. | Dataform MERGE-upsert. |
| `event_type_catalog` | ❌ Not managed by Dataform | ✅ Admin only: INSERT new types. | Direct INSERT. |
| `ministry_catalog` | ❌ Not managed by Dataform | ✅ Admin only: full CRUD. | Direct INSERT/UPDATE. |
| `ministry_memberships` | ❌ Not managed by Dataform | ✅ Admin only: full CRUD. | Direct INSERT/UPDATE. |

> **SCD2 PATCH rule:** All admin PATCH operations on SCD2 tables (`persons`, `person_contacts`, `person_occupations`, `victory_groups`) MUST follow the close-and-insert pattern: (1) `UPDATE` the current row → `valid_to = NOW(), is_current = FALSE`; (2) `INSERT` a new row with updated values, `valid_from = NOW()`, `valid_to = NULL`, `is_current = TRUE`, and the same `person_id` (stable UUID preserved). A plain `UPDATE` on an SCD2 table is a data integrity violation.

### Primary Terraform Resources

| Resource | Service | Purpose |
| :--- | :--- | :--- |
| `google_cloud_run_service` | Cloud Run | Hosts FastAPI backend API |
| `google_bigquery_dataset` | BigQuery | Bronze, Silver, Gold datasets |
| `google_dataform_repository` | Dataform | SQL pipeline Git repository connection |
| `google_dataform_repository_release_config` | Dataform | Compiles the `main` branch — used by all workflow invocations |
| `google_dataform_repository_workflow_config` | Dataform | Hourly scheduled pipeline run (Asia/Manila). Replaces Cloud Scheduler. |
| `google_pubsub_topic` | Pub/Sub | Attendance event message bus |
| `google_cloudfunctions_function` | Cloud Functions | `dataform-attendance-trigger` — Pub/Sub subscriber that chains compile → invoke for near-real-time attendance pipeline |
| `google_secret_manager_secret` | Secret Manager | Store API keys & Service Account JSON |
| `cloudflare_pages_project` | Cloudflare | Static frontend hosting |
| `google_service_account` | IAM | Least-privileged identity for Cloud Run, Dataform, Cloud Functions |

### Secret Manager Integration

All credentials accessed from Google Secret Manager at startup — never from environment variables or code. The Cloud Run service account is granted `secretmanager.secretAccessor` IAM role only for specific secrets it needs.

| Secret Name | Contents |
| :--- | :--- |
| `FIREBASE_SERVICE_ACCOUNT` | Firebase Admin SDK credentials |
| `BIGQUERY_PROJECT_ID` | GCP project identifier |
| `CORS_ALLOWED_ORIGINS` | Cloudflare Pages domain whitelist |
| `PUBSUB_TOPIC_ID` | Pub/Sub topic for Dataform triggers |
### CORS Policy

- Cloud Run FastAPI explicitly whitelists only the Cloudflare Pages domain.
- All other origins receive 403.
- `CORS_ALLOWED_ORIGINS` is stored in Secret Manager and injected at runtime.


## 8. Data Architecture — Bronze → Silver → Gold

### Medallion Architecture Overview

Copy
```plaintext
DATA SOURCES
────────────────────────────────────────────────────────────
📝 VG Leader Form   🎉 Event Registration   🔧 Admin Direct Entry
                              │
                    (Cloud Run API — streaming insert)
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│  BRONZE  (victory_bronze)                                │
│  Append-only. Never modified after write.                 │
│  Source of truth for all raw data.                        │
│                                                          │
│  raw_form_submissions · raw_event_actions                 │
│  raw_headcounts                                           │
└──────────────────────────────────────────────────────────┘
                              │
                    Dataform — SCD2 upsert
                    dedup by email + google_uid
                    Hourly (native) + Pub/Sub (immediate via Cloud Function)
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│  SILVER  (victory_silver)                                 │
│  Clean, normalized, versioned (SCD2).                    │
│  Source of truth for all reporting.                      │
│                                                          │
│  persons · person_contacts · person_roles                 │
│  person_occupations                                        │
│  equipping_classes · equipping_enrollments               │
│  event_type_catalog · events                             │
│  event_registrations · event_attendances                 │
│  headcounts                                              │
│  victory_groups · victory_group_members                  │
│  intern_relationships · ministry_catalog · ministry_memberships
│  person_relationships (Phase 2) · data_change_log        │
└──────────────────────────────────────────────────────────┘
                              │
                    Dataform — SQL views
                    Row access policies applied
                    Near real-time on silver update
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│  GOLD  (victory_gold)                                    │
│  Read-only views. Row security enforced.                 │
│  No raw data exposed.                                    │
│                                                          │
│  vw_member_demographics · vw_equipping_funnel            │
│  vw_equipping_completion · vw_equipping_cohorts          │
│  vw_event_participation · vw_person_engagement           │
│  vw_person_event_history · vw_victory_group_summary      │
│  vw_attendance_headcounts                                │
│  vw_leader_dashboard · vw_ministry_participation         │
│  vw_pastoral_events · vw_admin_full                      │
│  vw_business_network                                     │
└──────────────────────────────────────────────────────────┘
```
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    Looker Studio       Admin Portal    VG Leader Dashboard
    Executive reports   vw_admin_full   Row-filtered by
    BigQuery native     All mgmt views  SESSION_USER()
    connector
### Dataform (Bronze → Silver → Gold Pipeline)

Dataform is Google's SQL workflow tool built into BigQuery. You write `.sqlx` files in a GitHub repo and Dataform compiles them into a dependency graph, runs assertions, and executes them as BigQuery jobs.

**Trigger mechanisms:**

- **Dataform Native Schedule (`workflow_config`):** Dataform runs the full pipeline on a cron schedule (hourly, Asia/Manila timezone) using Dataform's built-in `release_config` + `workflow_config` resources — no Cloud Scheduler required. Managed via `google_dataform_repository_release_config` and `google_dataform_repository_workflow_config` in Terraform.
- **Pub/Sub + Cloud Function:** When Cloud Run publishes an attendance event, a lightweight Cloud Function (`dataform-attendance-trigger`) is invoked. The function fetches the latest compilation result from the `release_config` and calls the Dataform `workflowInvocations` API scoped to `stg_attendances.sqlx` and `discipleship_pipeline.sqlx` only — bypassing the hourly schedule window for near-real-time discipleship updates.

### Transformation Graph

| SQLX File | Layer | Source | Target | Trigger |
| :--- | :--- | :--- | :--- | :--- |
| `stg_persons.sqlx` | `2_silver` | `bronze.raw_form_submissions` | `silver.persons` (SCD2 upsert) | Scheduled (hourly, Dataform native) |
| `stg_contacts.sqlx` | `2_silver` | `bronze.raw_form_submissions` | `silver.person_contacts` | Scheduled (hourly, Dataform native) |
| `stg_occupations.sqlx` | `2_silver` | `bronze.raw_form_submissions` | `silver.person_occupations` | Scheduled (hourly, Dataform native) |
| `stg_victory_groups.sqlx` | `2_silver` | `bronze.raw_form_submissions` | `silver.victory_groups` | Scheduled (hourly, Dataform native) |
| `stg_vg_members.sqlx` | `2_silver` | `bronze.raw_form_submissions` | `silver.victory_group_members` | Scheduled (hourly, Dataform native) |
| `stg_intern_relationships.sqlx` | `2_silver` | `bronze.raw_form_submissions` | `silver.intern_relationships` — always INSERTs a new `pending` record for each intern named in Section 3 of a leader form submission. No MERGE/dedup is applied. For each record, attempts a case-insensitive exact match of the typed intern first + last name against `silver.persons` (WHERE `is_current = TRUE`): if exactly one match is found, `intern_person_id` is populated; if zero or multiple matches are found, `intern_person_id` is set to NULL and the record appears in the admin "Unresolved Interns" queue. `intern_first_name` and `intern_last_name` are always stored as typed. Admin reviews all pending and unresolved records in the admin review queue. | Scheduled (hourly, Dataform native) |
| `stg_events.sqlx` | `2_silver` | `bronze.raw_event_actions` (action_type = 'created') | `silver.events` | Scheduled (hourly, Dataform native) |
| `stg_registrations.sqlx` | `2_silver` | `bronze.raw_event_actions` (action_type = 'registered') | `silver.event_registrations` | Scheduled (hourly, Dataform native) |
| `stg_attendances.sqlx` | `2_silver` | `bronze.raw_event_actions` (action_type = 'attended') | `silver.event_attendances` | Pub/Sub (immediate, via Cloud Function) |
| `stg_headcounts.sqlx` | `2_silver` | `bronze.raw_headcounts` | `silver.headcounts` | Scheduled (hourly, Dataform native) |
| `discipleship_pipeline.sqlx` | `2_silver` | `silver.event_attendances` + `silver.event_type_catalog` + `silver.equipping_enrollments` + `silver.equipping_classes` | `silver.equipping_enrollments` — UPDATES existing `enrolled` records to `completed`. Never creates new enrollment records. No-op when `equipping_step IS NULL`. | Pub/Sub (immediate, via Cloud Function) |
| `gold_demographics.sqlx` | `3_gold` | `silver.persons` | `gold.vw_member_demographics` | Scheduled (hourly, Dataform native) |
| `gold_events.sqlx` | `3_gold` | `silver.events` + `silver.event_attendances` | `gold.vw_event_participation` | Scheduled (hourly, Dataform native) |
| `gold_headcounts.sqlx` | `3_gold` | `silver.headcounts` + `silver.events` | `gold.vw_attendance_headcounts` | Scheduled (hourly, Dataform native) |
| `gold_funnel.sqlx` | `3_gold` | `silver.equipping_enrollments` + `silver.equipping_classes` + `silver.persons` | `gold.vw_equipping_funnel` | Scheduled (hourly, Dataform native) |
| `gold_vg_summary.sqlx` | `3_gold` | `silver.victory_groups` + `silver.victory_group_members` | `gold.vw_victory_group_summary` | Scheduled (hourly, Dataform native) |
| `gold_engagement.sqlx` | `3_gold` | `silver.event_attendances` + `silver.event_registrations` | `gold.vw_person_engagement` | Scheduled (hourly, Dataform native) |
| `gold_event_history.sqlx` | `3_gold` | `silver.event_attendances` + `silver.event_registrations` + `silver.events` + `silver.equipping_enrollments` | `gold.vw_person_event_history` | Scheduled (hourly, Dataform native) |
| `gold_equipping_completion.sqlx` | `3_gold` | `silver.equipping_enrollments` + `silver.persons` | `gold.vw_equipping_completion` | Scheduled (hourly, Dataform native) |
| `gold_equipping_cohorts.sqlx` | `3_gold` | `silver.equipping_classes` + `silver.equipping_enrollments` | `gold.vw_equipping_cohorts` | Scheduled (hourly, Dataform native) |
| `gold_leader_dashboard.sqlx` | `3_gold` | `silver.victory_groups` + `silver.victory_group_members` + `silver.equipping_enrollments` + `silver.event_attendances` + `silver.ministry_memberships` | `gold.vw_leader_dashboard` | Scheduled (hourly, Dataform native) |
| `gold_ministry_participation.sqlx` | `3_gold` | `silver.ministry_memberships` + `silver.ministry_catalog` | `gold.vw_ministry_participation` | Scheduled (hourly, Dataform native) |
| `gold_pastoral_events.sqlx` | `3_gold` | `silver.events` + `silver.event_registrations` + `silver.persons` | `gold.vw_pastoral_events` | Scheduled (hourly, Dataform native) |
| `gold_admin_full.sqlx` | `3_gold` | `silver.persons` + `silver.person_occupations` + `silver.person_contacts` + `silver.equipping_enrollments` + `silver.victory_groups` + `silver.ministry_memberships` | `gold.vw_admin_full` | Scheduled (hourly, Dataform native) |
| `gold_business_network.sqlx` | `3_gold` | `silver.persons` + `silver.person_occupations` | `gold.vw_business_network` | Scheduled (hourly, Dataform native) |

> **Trigger note:** "Scheduled (hourly, Dataform native)" means the file runs as part of the full `workflow_config` cron run. "Pub/Sub (immediate, via Cloud Function)" means the file is also invoked as a scoped partial run when Cloud Function `dataform-attendance-trigger` fires — in addition to the hourly run.

**Dataform assertions:** Each `.sqlx` file includes assertions that verify data quality before writing to the next layer (e.g. `assert person_id IS NOT NULL`, `assert email matches regex pattern`). A failing assertion stops the pipeline and sends an alert — bad data never reaches Gold.

### Gold View Dependency DAG

Gold views must be processed in dependency order during Dataform compilation. All Gold views in this system read exclusively from Silver tables — there are **zero Gold-on-Gold view dependencies**. Any future Gold-on-Gold chain MUST be reviewed by `@architect` and documented here before implementation.

**All Gold views — Tier 1 (direct Silver dependencies only):**

| Gold SQLX File | Silver Sources |
| :--- | :--- |
| `gold_demographics.sqlx` | `silver.persons` |
| `gold_headcounts.sqlx` | `silver.headcounts` + `silver.events` |
| `gold_vg_summary.sqlx` | `silver.victory_groups` + `silver.victory_group_members` |
| `gold_ministry_participation.sqlx` | `silver.ministry_memberships` + `silver.ministry_catalog` |
| `gold_pastoral_events.sqlx` | `silver.events` + `silver.event_registrations` + `silver.persons` |
| `gold_business_network.sqlx` | `silver.persons` + `silver.person_occupations` |
| `gold_equipping_completion.sqlx` | `silver.equipping_enrollments` + `silver.persons` |
| `gold_equipping_cohorts.sqlx` | `silver.equipping_classes` + `silver.equipping_enrollments` |
| `gold_events.sqlx` | `silver.events` + `silver.event_attendances` |
| `gold_engagement.sqlx` | `silver.event_attendances` + `silver.event_registrations` |
| `gold_event_history.sqlx` | `silver.event_attendances` + `silver.event_registrations` + `silver.events` + `silver.equipping_enrollments` |
| `gold_funnel.sqlx` | `silver.equipping_enrollments` + `silver.equipping_classes` + `silver.persons` |
| `gold_leader_dashboard.sqlx` | `silver.victory_groups` + `silver.victory_group_members` + `silver.equipping_enrollments` + `silver.event_attendances` + `silver.ministry_memberships` |
| `gold_admin_full.sqlx` | `silver.persons` + `silver.person_occupations` + `silver.person_contacts` + `silver.equipping_enrollments` + `silver.victory_groups` + `silver.ministry_memberships` |

> **Rule:** If a future Gold view needs to reference another Gold view, that dependency MUST be declared in this table and reviewed by `@architect` before implementation. Gold-on-Gold chains increase compilation complexity and latency — they are currently forbidden without explicit approval.

### Pub/Sub Message Payload (Attendance → Dataform Trigger)

When `POST /api/events/{id}/attend` writes an attendance record, Cloud Run publishes a Pub/Sub message to `attendance-events-topic`. A Cloud Function subscribed to this topic invokes the Dataform `workflowInvocations` API, triggering an immediate partial run of the attendance and discipleship pipeline — bypassing the hourly Dataform native schedule for near-real-time updates.

**Publisher:** Cloud Run backend (`google-cloud-pubsub` client)
**Topic:** `attendance-events-topic` (Terraform resource: `google_pubsub_topic.attendance_events`)
**Subscriber:** Cloud Function `dataform-attendance-trigger` (Pub/Sub push subscription) → fetches the latest `compilationResult` from the Dataform `release_config` → calls `workflowInvocations` API scoped to `stg_attendances.sqlx` and `discipleship_pipeline.sqlx` only.

**Why a Cloud Function (not a direct Dataform push subscription):** Triggering a Dataform workflow invocation requires two sequential API calls — first fetching the latest compilation result, then creating the invocation. A Cloud Function handles this two-step chain cleanly and stays within the free tier (< 10 invocations/day). The function is a lightweight ~30-line Python script and is Terraform-managed via `google_cloudfunctions_function.dataform_attendance_trigger`.

**Message envelope (Google Pub/Sub JSON):**
```json
{
  "messageId": "string",
  "publishTime": "ISO-8601 timestamp",
  "attributes": {
    "event_type": "attendance",
    "event_id": "<silver.events.event_id UUID>",
    "person_id": "<silver.persons.person_id UUID>",
    "attendance_id": "<silver.event_attendances.attendance_id UUID>"
  },
  "data": "<base64-encoded JSON payload>"
}
```

**Decoded `data` payload:**
```json
{
  "action": "attendance_recorded",
  "event_id": "uuid-string",
  "person_id": "uuid-string",
  "attendance_id": "uuid-string",
  "equipping_step": "spiritual_foundations | null",
  "triggered_at": "2025-02-15T14:00:00Z"
}
```

**Rules:**
- `equipping_step` MUST be included. Set to `null` if the event is not an equipping event — this short-circuits `discipleship_pipeline.sqlx` and avoids unnecessary pipeline execution.
- The Cloud Function invocation targets only `stg_attendances.sqlx` and `discipleship_pipeline.sqlx` (not a full warehouse run), bounded by `event_id` to minimize BigQuery slot usage.
- If the Cloud Function fails or the Pub/Sub message is not delivered within 5 minutes, the hourly Dataform native schedule provides a guaranteed catch-up run. The pipeline is idempotent — re-running produces the same result.

### Dataform Native Scheduling

Dataform's built-in scheduling is used instead of Cloud Scheduler. This avoids the two-step compile-then-invoke problem that Cloud Scheduler HTTP targets cannot solve in a single call.

**How it works:**

1. A `release_config` in Dataform is configured to point to the `main` Git branch. Dataform compiles the repository on each scheduled run automatically.
2. A `workflow_config` defines the cron schedule and which actions to run. It references the `release_config` — no manual compilation step needed.

**Terraform resources (managed in `terraform/main.tf`):**

```hcl
resource "google_dataform_repository_release_config" "main" {
  project       = var.project_id
  location      = var.region
  repository    = google_dataform_repository.main.name
  name          = "main"
  git_commitish = "main"
}

resource "google_dataform_repository_workflow_config" "scheduled" {
  project        = var.project_id
  location       = var.region
  repository     = google_dataform_repository.main.name
  name           = "scheduled-run"
  release_config = google_dataform_repository_release_config.main.id
  cron_schedule  = "0 * * * *"   # Hourly
  time_zone      = "Asia/Manila"
}
```

> **Schedule frequency:** Hourly is sufficient for routine Silver and Gold updates given current scale. Adjust `cron_schedule` in Terraform if business needs change — no code changes required.


## 9. Data Flow Diagram

### Data Entry Sources

Copy
```plaintext
VG Leader Form       Event Registration    Admin Direct Entry
/leader              /e/[slug]             Create Profile tool
Google Sign-In       Google Sign-In        Event / Class mgmt
       │                    │                    │
       └────────────────────┴────────────────────┘
                                         │
                        All sources write to Bronze first
                        via Cloud Run API (streaming insert)
```

### Bronze Tables

Copy
```plaintext
bronze.raw_form_submissions        bronze.raw_event_actions         bronze.raw_headcounts
───────────────────────────        ─────────────────────────        ───────────────────────
submission_id    UUID              action_id        UUID            headcount_id  UUID
google_uid       STRING            action_type      STRING          date          DATE
submitted_at     TIMESTAMP         performed_by     FK person_id    event_type    STRING
raw_payload      JSON              payload          JSON            event_id      FK / NULL
source_page      STRING            event_id         FK              attendee_count INT64
ip_hash          STRING                                             submitted_by  FK person_id
                                                                   submitted_at  TIMESTAMP
```

### Silver Tables (normalized, versioned)

Copy
```plaintext
silver.persons (SCD2 · core)              silver.person_occupations (SCD2)
─────────────────────────────             ──────────────────────────────────────
person_id · google_uid                    occupation_id · person_id
first_name · middle_name                  employment_type (employed|self_employed)
last_name · suffix · full_name            nature_of_work · company_name
email · address                   nature_of_business · business_name
is_in_victory_group                       valid_from · valid_to · is_current
vg_leader_first_name · vg_leader_last_name
journey_stage · review_status · source    silver.equipping_classes
one2one_completed · one2one_date          ──────────────────────────────────────
duplicate_flag · duplicate_of_person_id   class_id · canonical_step
profile_completeness_pct                  class_name · batch_code
gender · birthdate · civil_status         facilitator_person_id
valid_from · valid_to · is_current        start_date · end_date · capacity
                                          status: upcoming|ongoing|completed|cancelled

silver.victory_groups (SCD2)              silver.equipping_enrollments
──────────────────────────────────────    ──────────────────────────────────────
group_id · leader_person_id               enrollment_id · class_id · person_id
group_name · group_type                   step_name_as_completed
(single|wives|husbands|students|young_pro)enrollment_status: enrolled|completed|dropped
is_active                                 enrolled_at · completed_at · dropped_at
valid_from · valid_to · is_current

silver.victory_group_members              silver.event_registrations                silver.headcounts
──────────────────────────────────────    ──────────────────────────────────────    ──────────────────────────────────────
membership_id · group_id · person_id      registration_id · event_id · person_id    headcount_id · date · event_type
member_first_name · member_last_name      status: registered|attended|no_show|cancelled event_id · attendee_count
is_active · added_at · removed_at        payment_status · amount_paid · payment_ref submitted_by · submitted_at
                                          registered_at · registration_source
```

### Gold Views (read-only, row-secured)

| View Name | Audience |
| :--- | :--- |
| `gold.vw_member_demographics` | Executive + Admin |
| `gold.vw_equipping_funnel` | Executive + Admin |
| `gold.vw_equipping_completion` | Admin |
| `gold.vw_equipping_cohorts` | Admin |
| `gold.vw_event_participation` | Executive + Admin |
| `gold.vw_attendance_headcounts`| Executive + Admin |
| `gold.vw_person_engagement` | Executive + Admin |
| `gold.vw_person_event_history` | Admin + Leader (filtered) |
| `gold.vw_victory_group_summary` | Executive + Admin |
| `gold.vw_leader_dashboard` | VG Leader — `SESSION_USER()` row policy |
| `gold.vw_ministry_participation` | Executive + Admin |
| `gold.vw_pastoral_events` | Admin only |
| `gold.vw_admin_full` | Admin only |
| `gold.vw_business_network` | Admin only |

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

## 11. Security Architecture

Seven-layer defense-in-depth — no single point of failure.
### Access Control Layers

```plaintext
LAYER 1: Network       Cloudflare WAF (Bot Fight Mode + Geo-blocking)
LAYER 2: Auth          Firebase Auth (Google Sign-In only — no passwords)
                              │
                    (Cloud Run receives JWT)
                              │
                              ▼
LAYER 3: API Role      FastAPI Role-Based Access (RBAC)
                       Checks silver.person_roles table
                              │
                    (API requests BigQuery data)
                              │
                              ▼
LAYER 4: Database      BigQuery Row-Level Security
                       Filtered by SESSION_USER() email
```

| Layer | Technology | What It Protects Against | Configuration |
| :--- | :--- | :--- | :--- |
| 1 — Edge | Cloudflare WAF + DDoS | SQL injection, XSS, brute force, DDoS attacks, bots | Free managed ruleset + OWASP Core Rule Set enabled |
| 2 — Transport | HTTPS / TLS 1.3 (Cloudflare) | Man-in-the-middle, data interception, certificate spoofing | Full (strict) SSL mode, HSTS with 1-year max-age |
| 3 — Authentication | Firebase Auth (Google OAuth 2.0) | Unauthorized access, credential stuffing, password attacks | Google Sign-In only — no passwords to breach |
| 4 — Authorization | Cloud Run role middleware (FastAPI) | Privilege escalation, unauthorized API calls | JWT claims verified + role looked up in silver.person_roles on every request |
| 5 — Data | BigQuery Row Access Policies | Data leakage between personas | Leader can only query their own rows — enforced at DB engine, not app layer |
| 6 — Secrets | Google Secret Manager | Credential exposure in code, logs, or env vars | Secrets accessed at runtime only via IAM-scoped service account |
| 7 — Code | SonarCloud SAST + pip-audit | Vulnerable dependencies, insecure code patterns | Blocks merges with OWASP-classified vulnerabilities |
### BigQuery Row Access Policy — SQL Reference

Row access policies are defined in Terraform using `google_bigquery_row_access_policy` resources. The policies use `SESSION_USER()` to match the authenticated caller's email at query time.

> **Critical Looker Studio constraint:** Looker Studio connects to BigQuery using the **Looker Studio service account** (`looker-studio-sa`), NOT the individual viewer's Google identity. This means `SESSION_USER()` in a standard row access policy resolves to the service account email, NOT the viewer's email — breaking per-leader row filtering.
>
> **Approved solution for `vw_leader_dashboard`:** Configure the Looker Studio data source with **"Viewer's credentials"** mode (Zero Trust → Data Credentials → Viewer's credentials). In this mode, BigQuery receives queries under the viewer's own Google account identity, so `SESSION_USER()` resolves correctly. Each VG Leader MUST have `bigquery.filteredDataViewer` IAM role on the `victory_gold` dataset.
>
> **For executive/admin views** that do NOT need per-viewer filtering: use "Owner's credentials" (service account). Standard IAM dataset-level access applies.

#### Policy: VG Leader Dashboard (leader sees only their own rows)

```sql
-- Applied to: victory_gold.vw_leader_dashboard
-- Requires: Looker Studio data source configured with "Viewer's credentials"
CREATE OR REPLACE ROW ACCESS POLICY leader_row_filter
ON `victory_gold.vw_leader_dashboard`
GRANT TO ("domain:victorychurch.ph")
FILTER USING (leader_email = SESSION_USER());
```

#### Policy: Sensitive Events (admin-only for is_sensitive = TRUE rows)

```sql
-- Admins see all rows (no filter)
CREATE OR REPLACE ROW ACCESS POLICY admin_all_rows
ON `victory_gold.vw_pastoral_events`
GRANT TO ("group:admins@victorychurch.ph")
FILTER USING (TRUE);

-- Non-admin viewers see only non-sensitive rows
CREATE OR REPLACE ROW ACCESS POLICY non_sensitive_only
ON `victory_gold.vw_pastoral_events`
GRANT TO ("domain:victorychurch.ph")
FILTER USING (is_sensitive = FALSE);
```

**Terraform resource pattern:**
```hcl
resource "google_bigquery_row_access_policy" "leader_filter" {
  project      = var.project_id
  dataset_id   = "victory_gold"
  table_id     = "vw_leader_dashboard"
  policy_id    = "leader_row_filter"
  filter_predicate = "leader_email = SESSION_USER()"
  grantees     = ["domain:victorychurch.ph"]
}
```

> **IAM Reconciliation — Automated (periodic):** A scheduled reconciliation script runs hourly (or daily) to sync `bigquery.filteredDataViewer` IAM bindings with the current set of active VG Leaders in `silver.person_roles`. The script queries `silver.person_roles WHERE role = 'vg_leader' AND is_active = TRUE`, retrieves each leader's `email` from `silver.persons`, and applies the `google_bigquery_dataset_iam_member` binding for `victory_gold` via the GCP IAM API. Leaders whose `is_active` is set to `FALSE` are removed from the binding on the next reconciliation run. This eliminates the manual Terraform-per-leader action previously required. The reconciliation script is Terraform-managed as a Cloud Scheduler job + Cloud Function. See Decision Log 2026-02-24 (IAM reconciliation).

### Cloudflare Access (Admin Gate)

The /admin and /events pages are additionally protected by Cloudflare Access (free for up to 50 users). This adds a zero-trust authentication layer at the CDN edge — before the page even loads. Only email addresses in the approved list can access these paths. A valid Firebase Auth token is then also required to make any API calls.

**Email whitelist management procedure:**

The Cloudflare Access policy for `/admin` and `/events` is managed via the Cloudflare dashboard (Zero Trust → Access → Applications). The process:
1. Admin adds a new staff member's Google email to the Access policy "Allow" rule.
2. Admin removes departed staff members' emails from the "Allow" rule.

> **Click-Ops Exception (documented):** Cloudflare Access email whitelist management is the **only** permitted manual Cloudflare dashboard action. All other Cloudflare configuration (DNS, WAF rules, Pages project) remains Terraform-managed. This exception exists because storing email addresses in Terraform/Git raises privacy concerns. Capacity: free tier supports up to 50 unique users — sufficient for current admin team scale.

### Principle of Least Privilege — IAM Roles

| Service Account | BigQuery Role | Other Roles |
| :--- | :--- | :--- |
| Cloud Run (backend) | `bigquery.dataEditor` on `silver` only | `secretmanager.secretAccessor`, `pubsub.publisher` |
| Dataform | `bigquery.dataEditor` on `silver` + `gold`; `bigquery.dataViewer` on `bronze` | None additional |
| Cloud Functions (`dataform-attendance-trigger`) | None (calls Dataform API, not BigQuery directly) | `dataform.editor` on Dataform repository; `pubsub.subscriber` |
| Looker Studio | `bigquery.dataViewer` on `gold` dataset only | None additional |
| GitHub Actions (deploy) | None (Terraform manages BigQuery) | `run.admin`, `artifactregistry.writer`, `iam.serviceAccountUser` |
| GitHub Actions (Terraform) | `bigquery.admin` (for schema management only) | `resourcemanager.projectIamAdmin` (scoped) |

## 12. UX Flows
### Entry Points Summary

| Entry Point | URL | Who | Auth | Key Behavior | Phase |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Event Landing Page | `/e/[slug]` | Anyone | Google Sign-In | Smart pre-check → profile form or confirm or already-registered screen. VG question for new users. | Phase 1 |
| VG Leader Form | `/leader` | VG Leaders | Google Sign-In | New → blank form. Returning → full pre-fill. Captures personal info + groups + members. | Phase 1 |
| Admin Portal | `/admin` | Admin team | Google Sign-In + admin role | Review queue, event management, class roster management, person editing, role assignment. | Phase 1 |
| Reports | `/reports` | Executives | Google Sign-In + executive role | Embedded Looker Studio dashboards. No data editing. | Phase 1 |
| Member Profile | `/profile` | VG Members | Google Sign-In | View and update own record. Pre-fills from Silver. Collects employment info and VG Leader name (member-stage required fields). Cannot see other records. | Phase 1 |
| Pastoral Event Page | `/e/[slug]` | Families / couples | Google Sign-In | Simplified form capturing person being celebrated as primary record. | Phase 1 |

### Member Profile Form — `/profile.html`

Copy
```plaintext
1. Member opens /profile → Google Sign-In (one-tap if already signed in)
2. Frontend calls GET /api/me with JWT
3. Cloud Run looks up record by google_uid → returns full profile
4. Form pre-fills all known fields:
   Section 1 — Personal Info (Contact-stage fields, all read-only if already complete)
   Section 2 — Employment Info (Employment Type → conditional fields)
   Section 3 — VG Leader (their leader's first and last name)
5. Member updates or completes fields → submits
6. POST /api/submit → writes to bronze.raw_form_submissions
7. Success message: "Thank you, your profile has been updated."
```

**Field display rules:**
- All Contact-stage fields (name, address, contact number, birthday, Facebook) are shown pre-filled and editable — members may correct their own data.
- Employment Type and conditional fields (Section 2) are always shown — these are the primary reason a member visits this page.
- VG Leader name fields (Section 3) are shown pre-filled if previously set and editable — the member may update if their leader changes.
- A member cannot view or edit any other person's record. The form is scoped strictly to `google_uid` of the signed-in user.

**Write path:** Identical to the VG Leader form — all updates write to `bronze.raw_form_submissions` with `source_page = 'profile'`. Dataform reconciles on the next scheduled run (SCD2 upsert on `silver.persons` and `silver.person_occupations`).

---

### VG Leader Form — Returning User Flow

Copy
```plaintext
1. Leader opens /leader → Google Sign-In (one-tap if already signed in)
2. Frontend calls GET /api/me with JWT
3. Cloud Run looks up record by google_uid → returns full profile + groups + members
4. Form pre-fills:
   Section 1 — Personal Info (all Member/Intern fields)
   Section 2 — Groups Led (one card per group, type + member list)
   Section 3 — Interns (confirmed interns shown with ✅, pending shown with clock icon)
5. Leader updates any fields, adds/removes members → submits
6. POST /api/submit → writes to bronze.raw_form_submissions
7. Success message: "Thank you, your data has been received."
8. Form resets
```
### VG Leader Form — Sections

Copy
```plaintext
┌─────────────────────────────────────────┐
│  SECTION 1 — Personal Information       │
│  First Name · Middle Name · Last Name   │
│  Suffix · Birthday · Address            │
│  Contact Number · Facebook Profile      │
│  Employment Type → conditional fields   │
│  VG Leader (their leader) First + Last  │
├─────────────────────────────────────────┤
│  SECTION 2 — Victory Groups Led         │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Group 1                         │    │
│  │ Type: [single ▾]               │    │
│  │ Members:                        │    │
│  │   • Maria Santos               │    │
│  │   • Pedro Reyes                │    │
│  │   • [+ Add Member]            │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Group 2                         │    │
│  │ Type: [young_pro ▾]            │    │
│  │ Members:                        │    │
│  │   • Ana Cruz                   │    │
│  │   • [+ Add Member]            │    │
│  └─────────────────────────────────┘    │
│                                         │
│  [+ Add Another Group]                  │
├─────────────────────────────────────────┤
│  SECTION 3 — Interns I'm Supervising    │
│  (Optional — add names of persons       │
│   you are currently discipling as       │
│   future VG leaders)                    │
│                                         │
│  • Juan Dela Cruz    (confirmed ✅)     │
│  • [+ Add Intern]                       │
│    First Name: [___] Last Name: [___]   │
├─────────────────────────────────────────┤
│          [ Submit ]                     │
└─────────────────────────────────────────┘
```

**Section 3 — Interns I'm Supervising (form behavior):**
- Additive via form. Leaders submit names of interns they are supervising.
- On pre-fill for returning leaders: confirmed interns (`review_status = 'approved'`, `is_active = TRUE`) are shown with a ✅ badge. Pending interns show as "Pending admin confirmation."
- Adding an intern via form creates a new `silver.intern_relationships` record with `review_status = 'pending'` and `source = 'leader_form'`. Admin confirms in the admin portal.
- Removal of interns is admin-managed only (not via form). Leaders cannot remove interns through the form — they communicate removals to admin directly.

### Event Registration Flow — Complete Decision Tree

Copy
```plaintext
Person opens /e/[slug]
        │
        ▼
   Event page loads (hero image, name, date, venue)
        │
        ▼
   Clicks "Register"
        │
        ▼
   Google Sign-In (one-tap if already signed in)
        │
        ▼
   Frontend calls GET /api/events/{slug}/pre-check
        │
        ▼
   ┌────────────────────────────────────────────┐
   │  Is person already registered for          │
   │  THIS event?                               │
   └──────────┬──────────────┬──────────────────┘
              │              │
           YES              NO
              │              │
              ▼              ▼
   ┌──────────────┐  ┌──────────────────────────┐
   │ SCREEN:      │  │  Does person exist in     │
   │ "Already     │  │  silver.persons?           │
   │ Registered"  │  └─────┬──────────────┬──────┘
   │              │        │              │
   │ Show:        │     YES              NO
   │ • Reg date   │        │              │
   │ • Status     │        ▼              ▼
   │ • Upcoming   │  ┌───────────┐  ┌───────────┐
   │   events     │  │ Profile   │  │ SCREEN:   │
   │              │  │ complete? │  │ Profile   │
   └──────────────┘  └──┬────┬──┘  │ Form      │
                        │    │     │ (Contact  │
                     YES    NO     │  fields + │
                        │    │     │  VG Q)    │
                        ▼    ▼     └─────┬─────┘
                  ┌────────┐ ┌────────┐  │
                  │SCREEN: │ │SCREEN: │  │
                  │Confirm │ │Complete│  │
                  │Register│ │Profile │  │
                  │as [Name│ │(pre-   │  │
                  │]       │ │filled) │  │
                  └───┬────┘ └───┬────┘  │
                      │          │       │
                      ▼          ▼       ▼
               ┌─────────────────────────────┐
               │  POST /api/events/{slug}/   │
               │  self-register              │
               └──────────┬──────────────────┘
                          │
                          ▼
               ┌─────────────────────────────┐
               │  SUCCESS SCREEN             │
               │                             │
               │  ✅ "You are registered     │
               │  for [Event Name]!"         │
               │                             │
               │  📅 Feb 15, 2025 · 2:00 PM │
               │  📍 Victory Taguig          │
               │                             │
               │  No payment instructions.   │
               │  No GCash/bank details.     │
               │  Clean confirmation only.   │
               └─────────────────────────────┘
```

### Scenario 1 — Brand New Person

Copy
```plaintext
1. Opens /e/date-talk-feb-2025
2. Google Sign-In prompt → signs in
3. GET /api/events/date-talk-feb-2025/pre-check → person_found: false
4. Frontend shows PROFILE FORM with Contact stage fields:
     ┌─────────────────────────────────────┐
     │  Complete your profile to register  │
     │                                     │
     │  First Name:  [auto from Google]    │
     │  Middle Name: [_______________]     │
     │  Last Name:   [auto from Google]    │
     │  Suffix:      [None ▾]             │
     │  Address:     [_______________]     │
     │  Contact #:   [_______________]     │
     │  Birthday:    [_______________]     │
     │  Facebook:    [_______________]     │
     │                                     │
     │  Are you part of a Victory Group?   │
     │  ( ) Yes   ( ) No                   │
     │                                     │
     │          [ Submit & Register ]       │
     └─────────────────────────────────────┘
5. Person fills form → submits
6. Backend — two-phase write (new-user registration exception):
     Phase 1 (immediate, synchronous):
       a. Cloud Run writes full profile to bronze.raw_form_submissions (standard write-path).
       b. Cloud Run immediately creates a minimal Silver person record directly:
          person_id (new UUID), google_uid, first_name, last_name,
          review_status = 'pending', source = 'event_registration',
          journey_stage = 'contact', is_current = TRUE, valid_from = NOW().
          This is the only permitted direct Silver write from Cloud Run — required so that
          the event registration FK (person_id) can be resolved without waiting for Dataform.
       c. Cloud Run creates silver.event_registrations using the new person_id.
       d. SUCCESS SCREEN returned to user immediately.
     Phase 2 (async, next Dataform run):
       Dataform stg_persons.sqlx processes the bronze.raw_form_submissions record and
       SCD2-upserts the full Silver person record (adding all remaining fields from the
       form payload). The existing minimal record is updated in-place — no duplicate created.
7. SUCCESS SCREEN (clean confirmation — no payment instructions)
```

> **Write-path exception:** Cloud Run normally writes only to Bronze. The two-phase write above is the single permitted exception: a minimal Silver record is created immediately to satisfy the `event_registrations.person_id` FK and provide an instant confirmation. The Dataform pipeline then reconciles the full record on its next run. All new Bronze submissions must exist before the Silver minimal record is created — Bronze is always the authoritative source.

### Scenario 2 — Returning Person, Complete Profile, NOT Registered

Copy
```plaintext
1. Opens /e/date-talk-feb-2025
2. Google Sign-In (one-tap)
3. GET /api/events/date-talk-feb-2025/pre-check →
     person_found: true, profile_complete: true, already_registered: false
     upcoming_registrations: [Marriage Booster — Mar 1]
4. Frontend shows CONFIRM SCREEN:
     ┌─────────────────────────────────────┐
     │  Register as Juan Dela Cruz?        │
     │                                     │
     │  Event: Date Talk — Feb 2025        │
     │  📅 Feb 15, 2025 · 2:00 PM         │
     │  📍 Victory Taguig                  │
     │                                     │
     │         [ Confirm Registration ]    │
     │                                     │
     │  ─────────────────────────────────  │
     │  Your upcoming events:              │
     │  • Marriage Booster — Mar 1, 2025   │
     └─────────────────────────────────────┘
5. Clicks Confirm → POST /api/events/.../self-register
6. SUCCESS SCREEN (clean confirmation — no payment instructions)
```

### Scenario 3 — Returning Person, ALREADY Registered for This Event

Copy
```plaintext
1. Opens /e/date-talk-feb-2025
2. Google Sign-In (one-tap)
3. GET /api/events/date-talk-feb-2025/pre-check →
     person_found: true, already_registered: true
     existing_registration: { registered_at: "2025-01-20", status: "registered" }
     upcoming_registrations: [Date Talk — Feb 15, Marriage Booster — Mar 1]
4. Frontend shows ALREADY REGISTERED SCREEN:
     ┌─────────────────────────────────────┐
     │  ✅ You're already registered!      │
     │                                     │
     │  Hi Juan! You registered for        │
     │  Date Talk — Feb 2025 on            │
     │  January 20, 2025.                  │
     │                                     │
     │  📅 Feb 15, 2025 · 2:00 PM         │
     │  📍 Victory Taguig                  │
     │                                     │
     │  ─────────────────────────────────  │
     │  Your upcoming events:              │
     │  • Date Talk — Feb 15, 2025         │
     │  • Marriage Booster — Mar 1, 2025   │
     └─────────────────────────────────────┘
5. No register button. No duplicate submission possible.
```

### Scenario 4 — Returning Person, Incomplete Profile

Copy
```plaintext
1. Opens /e/date-talk-feb-2025
2. Google Sign-In (one-tap)
3. GET /api/events/date-talk-feb-2025/pre-check →
     person_found: true, profile_complete: false
     missing_fields: ["address", "facebook_profile"]
     already_registered: false
4. Frontend shows COMPLETE PROFILE SCREEN:
     ┌─────────────────────────────────────┐
     │  Complete your profile to register  │
     │                                     │
     │  First Name:  Juan       (filled)   │
     │  Middle Name: Santos     (filled)   │
     │  Last Name:   Dela Cruz  (filled)   │
     │  Suffix:      None       (filled)   │
     │  Address:     [_______________] ⚠️  │
     │  Contact #:   09171234567 (filled)  │
     │  Birthday:    1990-05-15  (filled)  │
     │  Facebook:    [_______________] ⚠️  │
     │                                     │
     │  Are you part of a Victory Group?   │
     │  (•) Yes   ( ) No         (filled)  │
     │                                     │
     │       [ Complete & Register ]        │
     └─────────────────────────────────────┘
5. Person fills missing fields → submits
6. Backend:
     a. Cloud Run writes updated profile fields to bronze.raw_form_submissions.
     b. The person already has a Silver record (person_id known from pre-check).
        Cloud Run creates silver.event_registrations immediately using the existing person_id —
        no direct Silver write needed. The person_id FK is already resolved.
     c. Dataform reconciles the profile update on the next scheduled run (SCD2 upsert adds missing fields).
     d. SUCCESS SCREEN returned to user immediately — no re-registration step required.
7. SUCCESS SCREEN (clean confirmation — no payment instructions)
```

### Success Screen — All Scenarios
The success screen is intentionally minimal. No payment instructions, no GCash numbers, no bank transfer details are shown on this screen.
Copy
```plaintext
┌─────────────────────────────────────┐
│                                     │
│            ✅                       │
│                                     │
│  You are registered for             │
│  Date Talk — February 2025!         │
│                                     │
│  📅 February 15, 2025 · 2:00 PM    │
│  📍 Victory Taguig                  │
│                                     │
│  See you there!                     │
│                                     │
└─────────────────────────────────────┘
```

Why no payment instructions on the success screen: Payment details (GCash numbers, bank accounts) are communicated through the church's existing channels — social media announcements, event descriptions, or in-person communication. The registration system focuses purely on confirming attendance intent. This keeps the success screen clean, reduces confusion, and avoids displaying sensitive financial information on a public-facing page.


### Admin Review Queue

Every record created by a public form or admin direct entry starts as `review_status = 'pending'`. The admin portal surfaces these records in a dedicated view.

The admin review queue is organized into four tabs, each surfacing a distinct category of records requiring action.

Copy
```plaintext
┌──────────────────────────────────────────────────────────────────┐
│  ADMIN REVIEW QUEUE                                              │
│  [ Pending Records (2) ] [ Duplicates (1) ] [ Unresolved        │
│    Interns (1) ] [ Interns Without Relationship (1) ]            │
│  ────────────────────────────────────────────────────────────    │
│                                                                  │
│  TAB 1 — PENDING RECORDS                                         │
│  New submissions awaiting admin review                           │
│                                                                  │
│  [ Maria Clara ]   Source: Form   Duplicate: NO                  │
│  [ Approve ] [ Reject ] [ Edit ]                                 │
│                                                                  │
│  ────────────────────────────────────────────────────────────    │
│                                                                  │
│  TAB 2 — DUPLICATES                                              │
│  Records where duplicate_flag = TRUE. Admin selects which        │
│  record to keep as canonical. The other is marked rejected.      │
│  Full merge is deferred to Phase 4.                              │
│                                                                  │
│  [ Juan Dela Cruz ]  Source: Event  Matches: Person #0001        │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐  │
│  │  THIS RECORD             │  │  EXISTING RECORD #0001       │  │
│  │  Source: event_reg       │  │  Source: admin_created       │  │
│  │  Created: Jan 20 2025    │  │  Created: Mar 10 2024        │  │
│  │  google_uid: linked      │  │  google_uid: none            │  │
│  └──────────────────────────┘  └──────────────────────────────┘  │
│  [ Keep This Record ] [ Keep #0001 ]                             │
│  Selecting "Keep" marks the other as review_status = 'rejected'  │
│  and sets duplicate_of_person_id on the rejected record.         │
│                                                                  │
│  ────────────────────────────────────────────────────────────    │
│                                                                  │
│  TAB 3 — UNRESOLVED INTERNS                                      │
│  intern_relationships records where intern_person_id = NULL.     │
│  Name was typed by a leader but could not be auto-matched.       │
│  Must be linked before the relationship can be approved.         │
│                                                                  │
│  [ "Anna Reyes" ]  Leader: Pedro Santos  Source: leader_form     │
│  Search: [_______________] → [ Link to Person ]                  │
│  [ Create New Contact Record ]                                   │
│                                                                  │
│  ────────────────────────────────────────────────────────────    │
│                                                                  │
│  TAB 4 — INTERNS WITHOUT ACTIVE RELATIONSHIP                     │
│  Persons with journey_stage = 'intern' but no approved,          │
│  active intern_relationships record.                             │
│                                                                  │
│  [ Ben Cruz ]  Stage: intern  No active relationship found       │
│  [ View Pending Relationships ] [ Create Relationship ]          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Duplicate resolution rules (Phase 1):**
- Admin reviews both records side by side and selects which to keep as the canonical record.
- The kept record retains its `person_id`, `google_uid`, and all history.
- The rejected record is set to `review_status = 'rejected'` and `duplicate_of_person_id = <canonical_person_id>`. It is excluded from all Gold view reporting.
- The rejected record's event registrations and history are **not merged** in Phase 1 — they are excluded from counts. Full merge with history re-attribution is deferred to Phase 4 (see Implementation Phases).
- Once a record is rejected as a duplicate, it is removed from the Duplicates tab and surfaced in a separate "Rejected Records" audit view accessible to admin only.

### Event Payment Flow

**Pre-registered (standard path):**
Copy
```plaintext
1. Person registers online → status = 'registered', payment_status = 'pending'
2. Registration success screen shows clean confirmation only — no payment instructions displayed (see Decision Log 2025-02-09)
3. Payment details are communicated through existing church channels (social media, announcements). Person pays externally.
4. Person brings receipt to physical counter OR sends to admin email
5. Admin looks up person in /events portal → clicks [ Mark Paid ] → enters Reference #, payment_method, amount_paid
6. payment_status = 'paid'. Status remains 'registered'.
7. Upon arrival at event venue: Admin clicks [ Attend ]
8. status → 'attended'. Discipleship pipeline triggers enrollment completion if applicable.
```

**Walk-in (no prior registration):**
Copy
```plaintext
1. Person arrives at venue without prior online registration.
2. Admin searches for person in /events portal → clicks [ Check In (Walk-in) ]
3. Backend auto-creates silver.event_registrations:
     status = 'registered', registration_source = 'admin'
     payment_status = 'pending' (paid events) | 'N/A' (free events)
     registered_at = check_in_timestamp
4. Backend immediately writes attendance to bronze.raw_event_actions.
5. Admin can subsequently update payment_status (paid / waived) and enter Reference # as needed.
6. Admin can also override walk-in registration details or create the registration entry manually
   before check-in if they prefer explicit control.
```

No payment gateway in Phase 1. All payment confirmation is manual. Payment instructions are never displayed on the registration success screen.


## 13. Schema Reference — All Tables
Bronze Layer — victory_bronze
bronze.raw_form_submissions
```sql
submission_id       STRING     NOT NULL  -- UUID, primary key
google_uid          STRING               -- Firebase Auth UID
submitted_at        TIMESTAMP  NOT NULL  -- Server-side timestamp
raw_payload         JSON       NOT NULL  -- Full form submission as JSON
source_page         STRING               -- Which page submitted (leader, event, profile, etc.)
ip_hash             STRING               -- SHA-256 hash of submitter IP (privacy-safe)
ingestion_timestamp TIMESTAMP  NOT NULL  -- Server-set BigQuery ingestion time. Used for table partitioning.
```
bronze.raw_event_actions
```sql
action_id           STRING     NOT NULL  -- UUID, primary key
action_type         STRING     NOT NULL  -- created|registered|attended|cancelled
performed_by        STRING     NOT NULL  -- FK → silver.persons.person_id. Semantics by action_type:
                                         --   created:    admin who created the event
                                         --   registered: the registrant's own person_id (self-reg) OR the admin's person_id (admin-reg)
                                         --   attended:   admin who marked attendance
                                         --   cancelled:  admin or the registrant who cancelled
performed_at        TIMESTAMP  NOT NULL  -- Server-side timestamp
payload             JSON                 -- Action-specific data
event_id            STRING               -- FK → silver.events.event_id
ingestion_timestamp TIMESTAMP  NOT NULL  -- Server-set BigQuery ingestion time. Used for table partitioning.
```
bronze.raw_headcounts
```sql
headcount_id        STRING     NOT NULL  -- UUID, primary key
date                DATE       NOT NULL  -- Date of the headcount
event_type          STRING     NOT NULL  -- e.g. "sunday_service", or the event category
event_id            STRING               -- FK → silver.events.event_id (NULL for Sunday Service headcounts)
attendee_count      INT64      NOT NULL  -- Anonymous total; no per-person records
submitted_by        STRING     NOT NULL  -- FK → silver.persons.person_id (admin)
submitted_at        TIMESTAMP  NOT NULL  -- Server-side timestamp
ingestion_timestamp TIMESTAMP  NOT NULL  -- Server-set BigQuery ingestion time. Used for table partitioning.
```

Silver Layer — victory_silver
silver.persons (SCD2 — core table)
```sql
-- Identity
person_id                   STRING     NOT NULL  -- UUID, stable primary key
google_uid                  STRING               -- Firebase Auth UID

-- Name (decomposed for PH naming conventions)
first_name                  STRING     NOT NULL
middle_name                 STRING               -- Mother's maiden name (common in PH)
last_name                   STRING     NOT NULL
suffix                      STRING               -- Jr., Sr., III, etc. NULL if not applicable
full_name                   STRING     NOT NULL  -- Computed: "first middle last suffix"

-- Contact (core — additional contacts via silver.person_contacts)
email                       STRING               -- Firebase Auth email. Retained here for auth-email matching when admin-created records claim their Google account on first sign-in (Decision Log 2026-02-24). Canonical contact store is silver.person_contacts.
address                     STRING               -- Full address, single text field

-- Victory Group membership (person-level attribute)
is_in_victory_group         BOOL                 -- Captured during event registration. NULL = not yet answered.
vg_leader_first_name        STRING               -- Their VG Leader's first name (member/intern stage)
vg_leader_last_name         STRING               -- Their VG Leader's last name (member/intern stage)

-- Journey
journey_stage               STRING     NOT NULL  -- contact|member|intern|leader — admin-set. Default: contact
one2one_completed           BOOL       DEFAULT FALSE
one2one_date                DATE                 -- NULL until completed
review_status               STRING     NOT NULL  -- pending|approved|rejected
source                      STRING               -- form_submission|event_registration|admin_created|pastoral_event
duplicate_flag              BOOL       DEFAULT FALSE
duplicate_of_person_id      STRING               -- FK → person_id of canonical record
profile_completeness_pct    INT64      DEFAULT 0 -- 0-100, computed by Silver pipeline per stage

-- Demographics
gender                      STRING               -- M|F|other
birthdate                   DATE
civil_status                STRING               -- single|married|widowed|separated

-- SCD2 columns
valid_from                  TIMESTAMP  NOT NULL
valid_to                    TIMESTAMP            -- NULL = current record
is_current                  BOOL       NOT NULL  DEFAULT TRUE
```
**Deduplication Algorithm (`stg_persons.sqlx`):**

Exact-match only — no fuzzy matching. A duplicate is flagged when ALL conditions are true:
- `first_name` (case-insensitive, trimmed) matches
- `last_name` (case-insensitive, trimmed) matches
- `birthdate` matches exactly
- `google_uid` values are **different** (same UID = same person, not a duplicate)
- Both records have `is_current = TRUE`

The canonical record is the older `person_id` (lower `valid_from`). Middle name is intentionally excluded from the match key — middle name capture is inconsistent during early data migration.

**Pipeline behavior:** Sets `duplicate_flag = TRUE` and `duplicate_of_person_id = <canonical_id>`. The pipeline never auto-merges. Admin reviews in the pending queue and manually resolves.

silver.person_contacts (SCD2)
```sql
contact_id      STRING     NOT NULL  -- UUID
person_id       STRING     NOT NULL  -- FK → silver.persons
contact_type    STRING     NOT NULL  -- mobile|home|work|email|facebook|instagram
contact_value   STRING     NOT NULL
valid_from      TIMESTAMP  NOT NULL
valid_to        TIMESTAMP            -- NULL = current record
is_current      BOOL       NOT NULL  DEFAULT TRUE
```
silver.person_occupations (SCD2)
```sql
occupation_id       STRING     NOT NULL  -- UUID
person_id           STRING     NOT NULL  -- FK → silver.persons
employment_type     STRING     NOT NULL  -- employed|self_employed

-- Fields for employed
nature_of_work      STRING               -- e.g. Accounting, Engineering, Teaching
company_name        STRING

-- Fields for self-employed
nature_of_business  STRING               -- e.g. Food, Retail, Graphic Design
business_name       STRING

-- SCD2 columns
valid_from          TIMESTAMP  NOT NULL
valid_to            TIMESTAMP            -- NULL = current record
is_current          BOOL       NOT NULL  DEFAULT TRUE
```

**Employment Conditional Enforcement (three layers):**
1. **Frontend:** Alpine.js `x-show` directives hide/clear the inapplicable field pair when `employment_type` is selected. Both field pairs cannot be visible simultaneously.
2. **Backend:** The `PersonOccupation` Pydantic model uses `@model_validator` to enforce: if `employment_type == 'employed'`, then `nature_of_business` and `business_name` must be `None`; if `employment_type == 'self_employed'`, then `nature_of_work` and `company_name` must be `None`. Returns HTTP 422 on violation.
3. **Dataform assertion** in `stg_occupations.sqlx`:
```sql
assert employed_fields_exclusive as (
  SELECT * FROM ${ref("person_occupations")}
  WHERE is_current = TRUE
  AND (
    (employment_type = 'employed'
      AND (nature_of_business IS NOT NULL OR business_name IS NOT NULL))
    OR
    (employment_type = 'self_employed'
      AND (nature_of_work IS NOT NULL OR company_name IS NOT NULL))
  )
)
```
A non-empty result from this assertion halts the pipeline.

Conditional fields: When employment_type = 'employed', nature_of_work and company_name are populated; nature_of_business and business_name are NULL. When employment_type = 'self_employed', the reverse applies. The Silver pipeline enforces this via assertions.

silver.person_roles (admin-managed)
```sql
role_id         STRING     NOT NULL  -- UUID
person_id       STRING     NOT NULL  -- FK → silver.persons
role            STRING     NOT NULL  -- admin|executive|vg_leader|vg_member
assigned_by     STRING     NOT NULL  -- FK → silver.persons (admin)
assigned_at     TIMESTAMP  NOT NULL
is_active       BOOL       NOT NULL  DEFAULT TRUE
```
silver.equipping_classes
```sql
class_id                STRING     NOT NULL  -- UUID
canonical_step          STRING     NOT NULL  -- victory_weekend|discipleship_class|
                                             -- spiritual_foundations|leadership_113
class_name              STRING     NOT NULL  -- e.g. "Spiritual Foundations Batch 12"
batch_code              STRING               -- e.g. "SF-2025-B12"
facilitator_person_id   STRING               -- FK → silver.persons
start_date              DATE       NOT NULL
end_date                DATE
capacity                INT64
status                  STRING     NOT NULL  -- upcoming|ongoing|completed|cancelled
created_by              STRING               -- FK → silver.persons (admin)
created_at              TIMESTAMP  NOT NULL
```
silver.equipping_enrollments
```sql
enrollment_id           STRING     NOT NULL  -- UUID
class_id                STRING     NOT NULL  -- FK → silver.equipping_classes
person_id               STRING     NOT NULL  -- FK → silver.persons
step_name_as_completed  STRING               -- Exact name on certificate (preserves "Leader's Lab")
enrollment_status       STRING     NOT NULL  -- enrolled|completed|dropped
enrolled_at             TIMESTAMP  NOT NULL
completed_at            TIMESTAMP            -- NULL until completed
dropped_at              TIMESTAMP            -- NULL unless dropped
drop_reason             STRING
notes                   STRING
created_by              STRING               -- FK → silver.persons (admin)
created_at              TIMESTAMP  NOT NULL
```
silver.event_type_catalog (admin-managed)
```sql
event_type_id   STRING   NOT NULL  -- UUID
type_name       STRING   NOT NULL  -- e.g. "Date Talk"
category        STRING   NOT NULL  -- equipping|event|pastoral_self|pastoral_admin|...
equipping_step  STRING             -- Canonical step name or NULL
is_paid         BOOL     NOT NULL  DEFAULT FALSE
default_price   NUMERIC
currency        STRING             -- "PHP"
```
silver.events (admin-managed)
```sql
event_id          STRING     NOT NULL  -- UUID
event_type_id     STRING     NOT NULL  -- FK → silver.event_type_catalog
event_name        STRING     NOT NULL
batch_code        STRING
start_datetime    TIMESTAMP  NOT NULL
end_datetime      TIMESTAMP
venue_name        STRING
capacity          INT64
is_paid           BOOL       NOT NULL  DEFAULT FALSE
price             NUMERIC
page_slug         STRING     UNIQUE    -- Auto-generated from event_name
hero_image_url    STRING               -- Canva export, uploaded by admin
is_sensitive      BOOL       NOT NULL  DEFAULT FALSE  -- TRUE for funerals
status            STRING     NOT NULL  -- registration_open|closed|completed|cancelled
created_by        STRING               -- FK → silver.persons (admin)
created_at        TIMESTAMP  NOT NULL
```
silver.event_registrations (self-register + admin)
```sql
registration_id       STRING     NOT NULL  -- UUID (deterministic hash of event_id + person_id for self-reg)
event_id              STRING     NOT NULL  -- FK → silver.events
person_id             STRING               -- FK → silver.persons (NULL if no account yet)
status                STRING     NOT NULL  -- registered|attended|no_show|cancelled
payment_status        STRING               -- pending|paid|waived|N/A
amount_paid           NUMERIC
payment_ref           STRING
payment_method        STRING               -- gcash|bank|cash|waived
payment_date          DATE
primary_person_name   STRING               -- Pastoral events: person being celebrated
registered_at         TIMESTAMP  NOT NULL
registration_source   STRING               -- self|admin|bulk
```

Duplicate registration prevention: For self-registrations, registration_id is computed as SHA256(event_id + ':' + person_id). This deterministic ID ensures that even if the API is called twice for the same person + event combination, only one registration record exists. The API also performs a pre-insert check and returns HTTP 409 if an active registration already exists.

silver.event_attendances (admin check-in)
```sql
attendance_id       STRING     NOT NULL  -- UUID
event_id            STRING     NOT NULL  -- FK → silver.events
person_id           STRING     NOT NULL  -- FK → silver.persons
registration_id     STRING               -- FK → silver.event_registrations (if pre-registered)
checked_in_at       TIMESTAMP  NOT NULL
check_in_method     STRING     NOT NULL  -- manual|qr_scan
checked_in_by       STRING               -- FK → silver.persons (admin)
session_tag         STRING               -- e.g. "morning" / "afternoon" for multi-session events
```
silver.victory_groups (SCD2)
```sql
group_id              STRING     NOT NULL  -- UUID
leader_person_id      STRING     NOT NULL  -- FK → silver.persons
group_name            STRING
group_type            STRING               -- single|wives|husbands|students|young_pro
is_active             BOOL       NOT NULL  DEFAULT TRUE
valid_from            TIMESTAMP  NOT NULL
valid_to              TIMESTAMP            -- NULL = current record
is_current            BOOL       NOT NULL  DEFAULT TRUE
```
silver.victory_group_members
```sql
membership_id         STRING     NOT NULL  -- UUID
group_id              STRING     NOT NULL  -- FK → silver.victory_groups
person_id             STRING               -- FK → silver.persons (NULL if member not yet in system)
member_first_name     STRING     NOT NULL  -- Captured from leader form
member_last_name      STRING     NOT NULL  -- Captured from leader form
is_active             BOOL       NOT NULL  DEFAULT TRUE
added_at              TIMESTAMP  NOT NULL
removed_at            TIMESTAMP            -- NULL = currently active
```

**Linking strategy:** `person_id` is NULL when the VG member has not yet been registered in the system. This allows leaders to submit member names immediately without requiring every member to have a system account first.

**Admin linking procedure:** The admin portal surfaces unlinked members (where `person_id IS NULL`) in a dedicated "Unlinked VG Members" queue accessible from `/admin`. For each unlinked member, the admin can:
1. **Search for existing person** — Admin types the member's name; system calls `GET /api/persons?q=<name>` to search `silver.persons`.
2. **Link** — Admin selects the matching person; calls `PATCH /api/vg-members/{membership_id}/link` with `{ "person_id": "<uuid>" }` (admin role required).
3. **Create new person** — If no match found, admin creates a new Contact-stage record; system auto-links after creation.
4. **Leave unlinked** — Admin can dismiss; `person_id` remains NULL and member name is captured but not linked.

silver.intern_relationships
```sql
relationship_id     STRING     NOT NULL  -- UUID, primary key
intern_person_id    STRING               -- FK → silver.persons. NULLABLE. NULL when the name typed by
                                         -- the VG Leader in Section 3 could not be auto-matched to a
                                         -- unique silver.persons record. Admin must link via
                                         -- PATCH /api/intern-relationships/{id}/link before approving.
intern_first_name   STRING     NOT NULL  -- First name as typed by the VG Leader on form submission.
                                         -- Preserved as audit trail regardless of resolution status.
intern_last_name    STRING     NOT NULL  -- Last name as typed by the VG Leader on form submission.
leader_person_id    STRING     NOT NULL  -- FK → silver.persons (the supervising VG Leader — must be a registered person)
start_date          DATE       NOT NULL
end_date            DATE                 -- NULL = currently active
is_active           BOOL       NOT NULL  DEFAULT TRUE
review_status       STRING     NOT NULL  DEFAULT 'pending'  -- pending|approved|rejected
                                         -- Records from leader_form start as 'pending'.
                                         -- Admin confirms → 'approved'. Only 'approved' records
                                         -- are used by stg_persons.sqlx to sync vg_leader display cache.
                                         -- A record with intern_person_id = NULL cannot be set to
                                         -- 'approved' — admin must link the person first.
source              STRING     NOT NULL  -- leader_form|admin_created
                                         -- 'leader_form': originated from VG Leader form Section 3.
                                         -- 'admin_created': entered directly by admin in admin portal.
```

**Relationship note:** This table is the canonical FK for the intern-leader data relationship. `leader_person_id` must be a registered `silver.persons` record. `intern_person_id` is nullable — it is resolved from the name typed by the VG Leader via auto-match or admin linking. A record with `intern_person_id = NULL` is considered unresolved and cannot be approved. The `vg_leader_first_name/last_name` on `silver.persons` serves as a display cache derived from this relationship by the Silver pipeline — only from records where `review_status = 'approved'` and `intern_person_id IS NOT NULL`. If multiple approved active records exist for the same intern, the most recent `start_date` is used. See Stage 03 and Decision Log 2026-02-24.

**Lifecycle management:**
- **Creation:** Dataform `stg_intern_relationships.sqlx` INSERTs a new `pending` record whenever a VG Leader names an intern in Section 3 of their form submission. Admin also creates records directly via `POST /api/intern-relationships` (admin-created, auto-approved).
- **Approval:** Admin sets `review_status = 'approved'` via `PATCH /api/intern-relationships/{id}`. The Silver pipeline syncs the `vg_leader_first_name/last_name` display cache on the intern's `silver.persons` record on the next scheduled run.
- **Duplicate pending records:** If the same intern is named across multiple leader form resubmissions, each generates a new `pending` record. Admin reviews the queue and rejects duplicates — only one `approved` record per active intern-leader pair should exist.
- **Closure (intern → leader promotion):** When an intern is promoted to VG Leader, admin must set `is_active = FALSE` and `end_date = today` via `PATCH /api/intern-relationships/{id}`. This is step 5 of the Stage 04 entry process. Without this, the former intern remains in active intern counts and in the supervising leader's form pre-fill indefinitely.
silver.ministry_catalog + silver.ministry_memberships
```sql
-- ministry_catalog
ministry_id      STRING  NOT NULL  -- UUID
ministry_name    STRING  NOT NULL
category         STRING             -- music|media|kids|ushering|prayer|...

-- ministry_memberships
membership_id    STRING     NOT NULL  -- UUID
ministry_id      STRING     NOT NULL  -- FK → silver.ministry_catalog
person_id        STRING     NOT NULL  -- FK → silver.persons
status           STRING     NOT NULL  -- interested|active|inactive
joined_at        TIMESTAMP
```
silver.person_relationships (Phase 2)
```sql
person_id_a           STRING  NOT NULL  -- FK → silver.persons
person_id_b           STRING  NOT NULL  -- FK → silver.persons
relationship_type     STRING  NOT NULL  -- spouse|parent_child|referred_by
```
silver.headcounts (admin-managed)
```sql
headcount_id    STRING     NOT NULL  -- UUID, primary key
date            DATE       NOT NULL  -- Date of the headcount
event_type      STRING     NOT NULL  -- e.g. "sunday_service", or the event category
event_id        STRING               -- FK → silver.events.event_id (NULL for Sunday Service headcounts)
attendee_count  INT64      NOT NULL  -- Anonymous total; no per-person records
submitted_by    STRING     NOT NULL  -- FK → silver.persons.person_id (admin)
submitted_at    TIMESTAMP  NOT NULL
```

silver.data_change_log (audit)
```sql
log_id       STRING     NOT NULL  -- UUID
table_name   STRING     NOT NULL
record_id    STRING     NOT NULL
changed_by   STRING     NOT NULL  -- FK → silver.persons (admin)
changed_at   TIMESTAMP  NOT NULL
change_type  STRING     NOT NULL  -- insert|update|delete
old_value    JSON
new_value    JSON
```

Table Inventory Summary
| Dataset | Table | Type | Phase |
| :--- | :--- | :--- | :--- |
| `victory_bronze` | `raw_form_submissions` | Append-only | Phase 1 |
| `victory_bronze` | `raw_event_actions` | Append-only | Phase 1 |
| `victory_bronze` | `raw_headcounts` | Append-only | Phase 1 |
| `victory_silver` | `persons` | SCD2 | Phase 1 |
| `victory_silver` | `person_contacts` | SCD2 | Phase 1 |
| `victory_silver` | `person_occupations` | SCD2 | Phase 1 |
| `victory_silver` | `person_roles` | Admin-managed | Phase 1 |
| `victory_silver` | `equipping_classes` | Admin-managed | Phase 1 |
| `victory_silver` | `equipping_enrollments` | Admin-managed | Phase 1 |
| `victory_silver` | `event_type_catalog` | Admin-managed | Phase 1 |
| `victory_silver` | `events` | Admin-managed | Phase 1 |
| `victory_silver` | `event_registrations` | Self-register + admin | Phase 1 |
| `victory_silver` | `event_attendances` | Admin check-in | Phase 1 |
| `victory_silver` | `headcounts` | Admin-managed | Phase 1 |
| `victory_silver` | `victory_groups` | SCD2 | Phase 1 |
| `victory_silver` | `victory_group_members` | Leader form capture | Phase 1 |
| `victory_silver` | `intern_relationships` | Admin-managed | Phase 1 |
| `victory_silver` | `ministry_catalog` | Admin-managed | Phase 1 |
| `victory_silver` | `ministry_memberships` | Admin-managed | Phase 1 |
| `victory_silver` | `data_change_log` | Audit log | Phase 1 |
| `victory_silver` | `person_relationships` | Admin-managed | Phase 2 |
| `victory_gold` | All `vw_*` views | Read-only SQL views | Phase 1 |

## 14. Gold Views — Reporting Layer
All Gold views are read-only SQL views on BigQuery. Row access policies are enforced at the database engine level — not the application layer.

> **Binding rule — `review_status` filter:** Every Gold view that joins `silver.persons` **MUST** include the filter `WHERE persons.review_status != 'rejected'` (or equivalently `WHERE persons.review_status IN ('pending', 'approved')`). This is non-negotiable. Rejected records are duplicate persons that have been superseded by a canonical record — including them in any count, funnel, or engagement metric produces inflated and incorrect reporting. This filter is enforced via a Dataform assertion on each Gold SQLX file. Any Gold view missing this filter will fail the CI/CD quality gate.
>
> **Pending vs. approved in Gold views:** `pending` records (new submissions awaiting admin review) are included in Gold views by default so that newly registered event attendees and form submitters appear in reporting immediately. Admin reviews pending records and either approves or rejects them. Only `rejected` records are excluded.
| View Name | Audience | Description |
| :--- | :--- | :--- |
| `gold.vw_member_demographics` | Executive + Admin | Total members, gender split, age bands, marital status, occupation breakdown (employed vs. self-employed), journey stage counts, monthly new member trend. |
| `gold.vw_equipping_funnel` | Executive + Admin | High-level funnel: counts per step for old and new pathway. Completion rates. "Encouraged SF" count. Drill-down: individuals at each stage with name, journey stage, and days since last completed step. |
| `gold.vw_equipping_completion` | Admin | One row per person. Boolean flags for each canonical step. Completion status for old pathway, new pathway, and combined. encouraged_to_add_sf flag. Used for follow-up targeting. |
| `gold.vw_equipping_cohorts` | Admin | Per-batch: enrolled vs. completed vs. dropped, completion rate, facilitator, batch dates. Cohort tracking — who went through a class together. |
| `gold.vw_event_participation` | Executive + Admin | Per-event: registered, attended, no-show, attendance rate, revenue collected vs. expected. Filters out is_sensitive events from executive view. |
| `gold.vw_attendance_headcounts`| Executive + Admin | Overall anonymous headcount tracking for Sunday Services and general events over time. |
| `gold.vw_person_engagement` | Executive + Admin | Per person: total events attended, events in last 12 months, unique event types, first event date, most recent event date, engagement consistency score. |
| `gold.vw_person_event_history` | Admin + Leader (filtered) | Full chronological event timeline per person. Equipping classes shown separately from general events. Sensitive events excluded for non-admin. |
| `gold.vw_victory_group_summary` | Executive + Admin | Group count by type (single, wives, husbands, students, young_pro). Leader leaderboard. Member count per group. Intern counts. Groups with zero members flagged. |
| `gold.vw_leader_dashboard` | VG Leader | Row-level filtered by leader_email = SESSION_USER(). Own groups, member list per group, own equipping completion status, own event history, own ministry affiliations. |
| `gold.vw_ministry_participation` | Executive + Admin | Active vs. interested per ministry, monthly join trend, multi-ministry members. |
| `gold.vw_pastoral_events` | Admin only | All pastoral events including sensitive ones. Family contacts created. Follow-up status. Excluded from executive Looker Studio entirely. |
| `gold.vw_admin_full` | Admin only | Denormalized join of all silver entities. Includes journey_stage, review_status, duplicate_flag, equipping completion flags, engagement score, employment info, VG membership, and group leadership details. |
| `gold.vw_business_network` | Admin only | Purpose-built view for the Business & Professionals Network dashboard. Joins `silver.persons` + `silver.person_occupations` (is_current = TRUE). Exposes only: person_id, first_name, last_name, employment_type, nature_of_work, company_name, nature_of_business, business_name. Filtered to employed and self_employed records only. Least-privilege alternative to sourcing occupation granularity from vw_admin_full. |

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

## 17. Implementation Phases

| Phase | Focus | Scope |
| :--- | :--- | :--- |
| **Phase 1** | **Foundations & Core CRM + Event Registration** | Monorepo setup, Cloud Run container, BigQuery Bronze/Silver/Gold, Dataform pipeline, VG Leader Form (HTML/Alpine.js), Member Profile (`/profile.html` — employment info + VG leader name self-service), Admin Review Queue, Google Sign-In, Role-based access. Event Type Catalog, Public Landing Pages (`/e/[slug]`), Self-registration logic, Duplicate registration checking. |
| **Phase 2** | **Event Operations & Reporting** | Admin Event Management UI (create, edit, close events), Attendance tracking and check-in, Looker Studio executive dashboards. |
| **Phase 3** | **Discipleship Pipeline** | Equipping class cohorts, Enrollment logic, Discipleship milestones (SF, LW, LF), Looker Studio executives dashboards, Discipleship pipeline drill-downs. |
| **Phase 4** | **Automation & Scale** | Person merging logic, Audit logging (SCD2 data_change_log), Advanced engagement scoring (recency/frequency), Performance tuning. |
| **Phase 5** | **Member Engagement Dashboard** | Extended `/profile` page — digital badge collection, full event history timeline, ministry involvement summary, pathway progress display. |

All phases deploy through the same GitHub Actions pipeline. New features go through the same quality gates as the initial build. Infrastructure changes are planned via Terraform before any cloud resource is created or modified.


## 18. Decision Log

| Date | Decision | Rationale | Status |
| :--- | :--- | :--- | :--- |
| 2025-01-20 | Monorepo structure | Simplifies shared logic between Dataform, Terraform, and Backend. | ✅ Final |
| 2025-01-21 | Cloudflare Pages for Frontend | 100% free for static assets, unified Edge security (WAF). | ✅ Final |
| 2025-01-22 | SCD2 for Silver Layer | Preserves historical snapshots — critical for discipleship growth over time. | ✅ Final |
| 2025-01-23 | Deterministic Registration IDs | Simple, code-free duplicate prevention and idempotency. | ✅ Final |
| 2025-01-24 | 2025 Pathway Transition | Permanent validity for legacy steps prevents data loss. | ✅ Final |
| 2025-01-25 | Alpine.js + Bootstrap 5 | Zero build step, maximizes speed of development and low-power device support. | ✅ Final |
| 2025-01-26 | Firebase Auth with Google Sign-In | One-tap if already signed into device. Same button for all pages — role determines what you see after. | ✅ Final |
| 2025-01-27 | VG Leader / Member form access | Any Google account can submit. Admin reviews all new submissions before they go live (pending queue). | ✅ Final |
| 2025-01-28 | Returning user form experience | Form pre-fills with existing data from database. Matched by google_uid on load via GET /api/me. | ✅ Final |
| 2025-01-29 | Post-submission experience | Simple success message: "Thank you, your data has been received." Form resets. No profile page shown at this stage. | ✅ Final |
| 2025-01-30 | Event attendance for large events | Phase 1: one-by-one check-in in admin UI. Phase 2: QR scan check-in. Same schema supports both — no changes needed when QR scan ships. | ✅ Final |
| 2025-01-31 | Person relationships (couples, parents) | Phase 2. Every person is an independent record in Phase 1. silver.person_relationships table added in Phase 2. | ✅ Final |
| 2025-02-01 | Existing data migration approach | Admin "Create Profile" tool for all migrated records. Migrated records claim their Google account on first sign-in by email match. | ✅ Final |
| 2025-02-02 | Role promotion (member → leader) | Always admin-managed. System never auto-promotes. Person submits leader form → admin reviews → admin assigns vg_leader role. | ✅ Final |
| 2025-02-03 | Automated notifications | None in Phase 1. No outbound emails. Keep it simple. | ✅ Final |
| 2025-02-04 | Duplicate record handling | System flags by name + birthday match across different google_uid values. Alert lists both records in admin queue. Admin edits correct record and deletes duplicate. No auto-merge. | ✅ Final |
| 2025-02-05 | Executive reports access | Looker Studio dashboards embedded inside /reports page. Google account already signed in = silent auth in iframe — no second login. | ✅ Final |
| 2025-02-06 | Event landing pages | Standalone pages at /e/[slug] with no site navigation. Canva-designed hero image uploaded by admin. New event = one admin action + one Canva image. Zero code. | ✅ Final |
| 2025-02-07 | Incomplete profile at event registration | Redirected to complete profile first. Registration auto-confirmed on completion — person doesn't need to re-register. | ✅ Final |
| 2025-02-08 | Payment for paid events | External (GCash / bank). Admin manually marks as paid with reference number, date, method. Payment status: pending → paid / waived. No payment gateway in Phase 1. | ✅ Final |
| 2025-02-09 | Payment instructions on success screen | Not shown. The registration success screen displays only a clean confirmation (event name, date, venue). No GCash numbers, no bank details, no payment instructions. Payment details are communicated through the church's existing channels. | ✅ Final |
| 2025-02-10 | Victory Group question at event registration | The event registration profile form includes "Are you part of a Victory Group?" (Yes/No). Stored on silver.persons.is_in_victory_group. Asked for new users during profile creation and for returning users with incomplete profiles. Not re-asked for returning users with complete profiles. | ✅ Final |
| 2025-02-11 | Duplicate event registration prevention | System performs a pre-check (GET /api/events/{slug}/pre-check) before allowing registration. If a person is already registered for an event, the frontend displays "You are already registered" with their registration date and status. The API returns HTTP 409 on duplicate submission. Registration IDs are deterministic (hash of event_id + person_id) for idempotency. | ✅ Final |
| 2025-02-12 | Upcoming events for returning registrants | When a returning person visits an event page and signs in, the pre-check endpoint returns a list of all their upcoming event registrations. This list is shown on both the confirm-registration screen and the already-registered screen. | ✅ Final |
| 2025-02-13 | Person name fields | Names are decomposed into first_name, middle_name, last_name, and suffix on silver.persons. full_name is computed by the Silver pipeline. This supports PH naming conventions where middle name (mother's maiden name) is standard. | ✅ Final |
| 2025-02-14 | Required fields by stage | Contact: first name, middle name, last name, suffix, address, contact number, birthday, Facebook profile. Member/Intern adds: employment info (type + conditional fields), VG leader name. Leader adds: groups led (type + member names). | ✅ Final |
| 2025-02-15 | Employment data model | silver.person_occupations (SCD2) with employment_type (employed / self_employed). Employed → nature_of_work + company_name. Self-employed → nature_of_business + business_name. Conditional fields — only the applicable pair is populated. | ✅ Final |
| 2025-02-16 | Victory Group types | single · wives · husbands · students · young_pro. Stored on silver.victory_groups.group_type. One group = one type. A leader can lead multiple groups of different types. | ✅ Final |
| 2025-02-17 | VG member capture on leader form | Leaders enter member names (first + last) per group. Stored in silver.victory_group_members. person_id is NULL until admin links the member to an existing person record. Allows immediate name capture without requiring members to have system accounts. | ✅ Final |
| 2025-02-18 | Equipping Pathway terminology | Called "Equipping Pathway." New steps: One2One + Spiritual Foundations + Leadership 113. Old steps: One2One + Victory Weekend + Discipleship Class + Leadership 113. | ✅ Final |
| 2025-02-19 | Leader's Lab historical naming | Leader's Lab = Discipleship Class. Canonical step: discipleship_class. step_name_as_completed field preserves the exact name on the certificate. | ✅ Final |
| 2025-02-20 | Equipping Pathway data entry | Admin-managed only. VG Leaders and Members are never asked about pathway completion on forms. Admin creates class batches and manages enrollment rosters. | ✅ Final |
| 2025-02-21 | Old pathway completers + new pathway | Both pathways permanently valid. Old pathway completers encouraged (not required) to complete Spiritual Foundations. System flags them with "Encourage SF" in admin view. | ✅ Final |
| 2025-02-22 | Equipping batch tracking | Track specific batch (cohort identity) AND report on step completion regardless of batch. silver.equipping_classes holds batch identity. Gold views aggregate on canonical_step. | ✅ Final |
| 2025-02-23 | One2One operational model | Personal meeting, not tracked as an event. Recorded as two fields on silver.persons: one2one_completed (BOOL) and one2one_date (DATE). Admin sets these. | ✅ Final |
| 2025-02-24 | Pathway candidate tracking view | Both: high-level funnel with counts per step AND drill-down to individual names per stage. Funnel in Looker Studio, names list in admin portal. | ✅ Final |
| 2025-02-25 | Event categories | Events (Date Talk, Marriage Booster, etc.), Equipping Pathway classes, Pastoral self-register (Weddings, Dedications), Pastoral admin-only (Funerals). Future: Outreach, Worship, Youth, Fellowship. | ✅ Final |
| 2025-02-26 | Events profile impact | Attendance records only. No milestone update. Contributes to engagement score surfaced in gold.vw_person_engagement. | ✅ Final |
| 2025-02-27 | Pastoral events — who enters data | Mix: Weddings and Dedications can self-register. Funerals are always admin-entered and flagged is_sensitive = TRUE. | ✅ Final |
| 2025-02-28 | Pastoral events — who gets captured | The person being celebrated (baby at dedication, couple at wedding). Created as contact stage records if no existing match by email. | ✅ Final |
| 2025-03-01 | Person journey stages | Four admin-managed stages: contact → member → intern → leader. Never auto-computed. | ✅ Final |
| 2025-03-02 | journey_stage computation | Admin-managed field only. System surfaces data to inform pastoral judgment; it never replaces it. | ✅ Final |
| 2026-02-24 | Remove `phone` from `silver.persons` | `phone` is canonically stored in `silver.person_contacts (type: mobile)`. Denormalization removed to eliminate dual-write ambiguity. `email` is retained on `silver.persons` exclusively for Firebase Auth account-matching — when admin-created records are claimed by their owner on first sign-in, the system matches by email. All other contact channels live in `silver.person_contacts`. | ✅ Final |
| 2026-02-24 | Intern-leader data relationship | `vg_leader_first_name/last_name` on `silver.persons` is a display cache valid for all stages and may reference a leader not yet registered in the system. `silver.intern_relationships.leader_person_id` is the canonical FK for the intern-leader relational link — both parties must be registered persons. The Silver pipeline keeps the display cache in sync from the linked leader record when `leader_person_id` is populated. | ✅ Final |
| 2026-02-24 | Artifact Registry latest-only retention | Artifact Registry stores only the `:latest` Docker image tag for Cloud Run. Prior versions are pruned automatically via Terraform-managed cleanup policy. This keeps storage perpetually under the 0.5 GB free-tier limit. Rollback is achieved via git revert + redeploy, not image version management in the registry. | ✅ Final |
| 2026-02-24 | Event landing pages in Phase 1 | Public landing pages (`/e/[slug]`), self-registration logic, and duplicate registration checking are Phase 1 scope — they are required to capture new contacts at the earliest stage. Admin Event Management UI and attendance tracking move to Phase 2. | ✅ Final |
| 2026-02-24 | Dataform scheduling — native over Cloud Scheduler | Dataform native `release_config` + `workflow_config` used for scheduled pipeline runs (hourly). Cloud Scheduler is not used — it cannot chain the two required API calls (compilationResults → workflowInvocations) in a single HTTP target. Dataform native handles this internally with no custom orchestration. | ✅ Final |
| 2026-02-24 | Pub/Sub → Dataform via Cloud Function | A Cloud Function (`dataform-attendance-trigger`) bridges Pub/Sub attendance events to the Dataform `workflowInvocations` API. Required because triggering a Dataform invocation is a two-step operation (fetch latest compilationResult → create invocation). The function is ~30 lines of Python, runs within free tier, and is Terraform-managed. | ✅ Final |
| 2026-02-24 | Discipleship pipeline — UPDATE, not CREATE | `discipleship_pipeline.sqlx` does not auto-create `equipping_enrollments` records. Events and equipping classes are separate systems; equipping enrollment is admin-managed via class rosters. The pipeline UPDATES existing `enrolled` records to `completed` when attendance is confirmed. Admin must enroll before attendance can trigger a completion. | ✅ Final |
| 2026-02-24 | Intern relationships — leader form + admin confirmation | VG Leaders identify their interns via VG Leader form Section 3. This creates pending `intern_relationships` records. Admins review and confirm in the admin portal (`review_status = 'approved'`). Only approved relationships are used by the Silver pipeline to sync the `vg_leader` display cache on `silver.persons`. Removal is admin-managed only. | ✅ Final |
| 2026-02-24 | New-user event registration — two-phase write | To resolve the timing gap between a new user submitting their profile form and the Dataform pipeline creating their Silver record, Cloud Run immediately creates a minimal Silver person record (person_id, google_uid, first/last name, journey_stage, review_status) to allow immediate event registration FK resolution. The full Bronze record is reconciled by Dataform on the next scheduled run. This is the only permitted direct Silver write from Cloud Run. | ✅ Final |
| 2026-02-24 | Walk-in check-in auto-creates registration | When admin checks in a person at `POST /api/events/{id}/attend` and no prior registration exists, the backend auto-creates a `silver.event_registrations` record (`status = 'registered'`, `payment_status = 'pending'` for paid events or `'N/A'` for free events, `registration_source = 'admin'`). Admin can override payment status and details afterwards. | ✅ Final |
| 2026-02-24 | Event pre-check validates event status | `GET /api/events/{slug}/pre-check` verifies `silver.events.status = 'registration_open'` as the first backend step. If the event is closed, completed, or cancelled, the endpoint returns HTTP 410 Gone before any person lookup. This prevents registration for non-open events regardless of profile completeness or prior registration status. | ✅ Final |
| 2026-02-24 | Remove bulk import feature | `bronze.raw_bulk_imports` table and all bulk CSV import functionality removed. The feature added pipeline complexity without sufficient return — admin "Create Profile" tool covers all data migration needs. `source` values updated: `bulk_import` removed; `admin_created` covers all admin-entered records. `check_in_method` values updated: `bulk_import` removed. | ✅ Final |
| 2026-02-24 | Pre-check profile completeness JOIN | `GET /api/events/{slug}/pre-check` computes `profile_complete` by querying `silver.persons` AND LEFT JOINing `silver.person_contacts` for `contact_type = 'mobile'` (contact_number) and `contact_type = 'facebook'` (facebook_profile). `profile_completeness_pct` on `silver.persons` is used for reporting views only — not by the pre-check endpoint. | ✅ Final |
| 2026-02-24 | profile_completeness_pct timing limitation | For new users created via the two-phase write, `profile_completeness_pct` on `silver.persons` defaults to `0` until the next Dataform run (up to 1 hour). The pre-check endpoint computes completeness dynamically via JOINs to avoid returning a false incomplete status during this window. This limitation is accepted for Phase 1; a real-time update to `profile_completeness_pct` as part of the two-phase write may be considered in a future phase. | ✅ Final |
| 2026-02-24 | Self-register event status re-validation | `POST /api/events/{slug}/self-register` re-validates `silver.events.status = 'registration_open'` at the point of write (step 0 in the handler) to guard against the race condition where admin closes the event between the pre-check call and the registration submission. Returns HTTP 410 Gone if status has changed. | ✅ Final |
| 2026-02-24 | performed_by semantics in raw_event_actions | `bronze.raw_event_actions.performed_by` records the actor for each action type: `registered` = registrant's own `person_id` (self-reg) or admin's `person_id` (admin-reg); `attended` = admin who marked attendance; `created` = admin who created the event; `cancelled` = admin or registrant. NOT NULL — for self-registration, the registrant's newly created `person_id` (from the two-phase write) is used. | ✅ Final |
| 2026-02-24 | SCD2 admin PATCH rule | All admin PATCH operations on SCD2 Silver tables (`persons`, `person_contacts`, `person_occupations`, `victory_groups`) MUST use the close-and-insert pattern: close the current row (`valid_to = NOW()`, `is_current = FALSE`), then INSERT a new row with updated values, preserving the original `person_id`. A plain SQL UPDATE on an SCD2 table is a data integrity violation. See Write-Path Ownership Matrix (Section 7). | ✅ Final |
| 2026-02-24 | Write-path ownership matrix | A consolidated Write-Path Ownership Matrix was added to Section 7 (Backend) documenting which component (Dataform vs. Cloud Run) owns writes to each Silver table, and what write pattern (SCD2 vs. direct INSERT/UPDATE) is required. This resolves previously inconsistent statements about Silver write ownership across the document. | ✅ Final |
| 2026-02-24 | Intern relationship API endpoints | Three new admin endpoints added: `GET /api/intern-relationships` (list with status filter), `POST /api/intern-relationships` (admin-created, auto-approved), `PATCH /api/intern-relationships/{id}` (approve, reject, deactivate). These endpoints are required for the admin review queue to function for Stage 03 (VG Intern). | ✅ Final |
| 2026-02-24 | Person search endpoint | `GET /api/persons?q=<name>` added to API Route table. Used by admin in the VG member linking workflow and intern search. Minimum query length: 2 characters. Returns `silver.persons` records (`is_current = TRUE`) ordered by name relevance. | ✅ Final |
| 2026-02-24 | stg_intern_relationships always-insert behavior | `stg_intern_relationships.sqlx` always INSERTs a new `pending` record for each intern named in a leader form submission — no MERGE or deduplication is applied. If the same leader resubmits with the same intern named, a duplicate `pending` record is created. Admin resolves duplicates in the review queue by approving one and rejecting the rest. `intern_person_id` is auto-populated when the typed name resolves to exactly one match in `silver.persons`; it is NULL when zero or multiple matches exist (unresolved). Admin must link unresolved records before approving. | ✅ Final |
| 2026-02-24 | VG Leader promotion — sequential admin steps | Stage 04 entry now documents five explicit admin steps: (1) form submission, (2) record approval, (3) `vg_leader` role assignment, (4) `journey_stage = leader` update, (5) close prior `intern_relationships` record. Steps 3 and 4 must be performed in the same admin session. A mismatch between role and journey_stage is surfaced as a warning in the admin portal person record view. | ✅ Final |
| 2026-02-24 | Intern relationship closure on leader promotion | When an intern is promoted to VG Leader, admin must close their active `intern_relationships` record via `PATCH /api/intern-relationships/{id}` with `is_active = FALSE` and `end_date = today`. This is step 5 of Stage 04 entry. Without this step, the former intern remains in active intern counts and in the supervising leader's form pre-fill indefinitely. | ✅ Final |
| 2026-02-24 | VG Leader IAM reconciliation — automated | The `bigquery.filteredDataViewer` IAM binding for `victory_gold` is maintained by a periodic reconciliation script (hourly/daily) rather than per-leader manual Terraform actions. The script syncs the active `vg_leader` set from `silver.person_roles` to the IAM policy. Leaders with `is_active = FALSE` are removed on the next reconciliation. Managed as a Cloud Scheduler + Cloud Function, Terraform-provisioned. | ✅ Final |
| 2026-02-24 | `/profile.html` advanced to Phase 1 | VG Members (non-leaders) need a self-service path to submit employment info and VG Leader name in Phase 1 — data that is required at Member stage but not collected by any existing Phase 1 form. `/profile.html` is advanced from Phase 2 to Phase 1 scope, limited to: contact-stage field corrections, employment info (Section 2), and VG Leader name (Section 3). Writes to `bronze.raw_form_submissions` with `source_page = 'profile'`. Dataform reconciles via SCD2 upsert. Phase 5 retains the extended engagement dashboard features (badges, event timeline, pathway progress). | ✅ Final |
| 2026-02-24 | Facebook Profile — encouraged at Contact, required at Member | Facebook Profile is an encouraged field at Contact stage and does not block event registration. It becomes a required field from Member stage onward and is included in `profile_completeness_pct` calculations for Member, Intern, and Leader stages. | ✅ Final |
| 2026-02-24 | Member stage transition — VG Leader name soft-warning | When admin promotes a Contact to Member, the admin portal checks whether `vg_leader_first_name` and `vg_leader_last_name` are populated. If either is missing, a soft warning is displayed. The transition is not blocked — admin may proceed — but the warning ensures the gap is visible and the record surfaces with a low `profile_completeness_pct` in admin views. | ✅ Final |
| 2026-02-24 | Intern stage — unlinked intern alert queue | Persons with `journey_stage = 'intern'` but no `intern_relationships` record with `review_status = 'approved'` and `is_active = TRUE` are surfaced in a dedicated admin queue tab ("Interns Without Active Relationship"). Admin is prompted to approve a pending relationship or create one directly. | ✅ Final |
| 2026-02-24 | VG Leader promotion — atomic Steps 3 & 4 via single API action | Steps 3 (role assignment) and 4 (journey_stage update) of Stage 04 entry are executed as a single atomic operation via `POST /api/persons/{id}/promote-to-leader`. The admin portal exposes a single "Promote to VG Leader" button — not two separate controls. This eliminates the data inconsistency state where role and journey_stage are mismatched. | ✅ Final |
| 2026-02-24 | VG Leader promotion — Step 5 inline prompt | After the "Promote to VG Leader" action, the admin portal checks for active `intern_relationships` records for the person. If found, an inline prompt is displayed to close the relationship. The system does not auto-close — admin must explicitly act. The open relationship is re-surfaced as a warning until resolved. | ✅ Final |
| 2026-02-24 | intern_relationships — nullable intern_person_id with raw name capture | `silver.intern_relationships.intern_person_id` is nullable. When a VG Leader types an intern's name in Section 3 of their form, `stg_intern_relationships.sqlx` attempts a case-insensitive exact name match against `silver.persons`. If exactly one match is found, `intern_person_id` is populated automatically. If zero or multiple matches exist, `intern_person_id` is NULL and the record appears in the "Unresolved Interns" admin queue tab. `intern_first_name` and `intern_last_name` are always stored. Admin links unresolved records via `PATCH /api/intern-relationships/{id}/link`. A record with `intern_person_id = NULL` cannot be approved. This pattern is consistent with `silver.victory_group_members`. | ✅ Final |
| 2026-02-24 | Duplicate resolution — Phase 1 keep-one approach | When admin resolves a duplicate (duplicate_flag = TRUE), admin selects which record to keep as canonical. The other is set to `review_status = 'rejected'` and `duplicate_of_person_id` is set to point to the canonical record. The rejected record's history (event registrations, attendances) is excluded from all Gold views via the binding `review_status != 'rejected'` filter. History re-attribution (merging the rejected record's history into the canonical record) is deferred to Phase 4 (Person merging logic). The Admin Review Queue Duplicates tab exposes side-by-side record comparison with "Keep This Record" / "Keep Other Record" actions — the "Merge" button is a Phase 4 feature. | ✅ Final |
| 2026-02-24 | Gold views — binding review_status filter | All Gold views that join `silver.persons` MUST filter `WHERE persons.review_status != 'rejected'`. This prevents rejected duplicate records from inflating counts, funnels, and engagement metrics. `pending` records are included in Gold views. This rule is enforced via Dataform assertions on each Gold SQLX file and blocks CI/CD on violation. | ✅ Final |
| 2026-02-24 | VG Leader promotion — Dataform run prerequisite | Admin must wait until after the next Dataform pipeline run (up to 1 hour after the leader's form submission) before executing Steps 2–5 of Stage 04 entry. This ensures the leader's victory groups are present in `silver.victory_groups` before the promotion is completed. | ✅ Final |

Victory Church · Master Architecture Plan · v4.3 · Confidential — Internal Use Only

---

## 19. Naming Conventions & Consistency Standards

This section is the **authoritative and binding** source for all naming conventions across the Victory Discipleship system. All agents, engineers, and contributors MUST follow these rules. Any deviation requires an `@architect` review and a documented decision in Section 18 (Decision Log).

> **Enforcement:** These rules are cross-checked by `validate_structure.py` and `schema_lint.py` during every CI/CD run.

---

### 19.1 Data Architecture (BigQuery & Dataform)

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
| **Silver Pipeline SQLX File** | `<pipeline_name>.sqlx` (no prefix) | `discipleship_pipeline.sqlx` | For Silver-layer SQLX files that perform cross-table logic (not a simple Bronze→Silver staging transform). Lives in `data/definitions/2_silver/`. No `stg_` prefix. |
| **Gold View** | `vw_<business_domain>` | `vw_member_demographics`, `vw_attendance_trends` | `vw_` prefix explicitly denotes a read-only BigQuery view. |
| **Gold Dimension Table** | `dim_<entity>` | `dim_members`, `dim_ministry_teams` | OLAP-style dimension prefix. |
| **Gold Fact Table** | `fact_<event>` | `fact_attendance`, `fact_event_registrations` | OLAP-style fact prefix. |
| **Gold Aggregate/Report** | `agg_<topic>` or `rpt_<topic>` | `agg_monthly_stats`, `rpt_leader_headcounts` | For pre-aggregated reporting tables. |

> **Disambiguation:** `1_bronze`, `2_silver`, `3_gold` are **directory prefixes** inside `data/definitions/` for Dataform source file organization only. The actual BigQuery dataset identifiers are `victory_bronze`, `victory_silver`, and `victory_gold`. These are two separate naming conventions that co-exist and MUST NOT be confused. Every reference to a BigQuery dataset (in Terraform, SQLX files, Python code, and API routes) MUST use `victory_bronze`, `victory_silver`, or `victory_gold`.

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

### 19.2 Backend (Python / FastAPI)

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

### 19.3 Frontend (HTML / CSS / JS)

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

### 19.4 Infrastructure (Terraform & GCP)

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

### 19.5 Git & CI/CD

| Element | Convention | Example |
| :--- | :--- | :--- |
| **Branch Name** | `<type>/<kebab-case-description>` | `feature/member-search`, `fix/dataform-bug` |
| **Branch Types** | `feature/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/` | See `README.md` Section 3 |
| **Commit Message** | `<type>(<scope>): <short description>` | `feat(api): add person export endpoint` |
| **GitHub Actions Workflow File** | `kebab-case.yaml` | `deploy-backend.yaml`, `sonarqube-analysis.yaml` |
| **GitHub Actions Secret** | `UPPER_SNAKE_CASE` | `WIF_PROVIDER`, `GCP_PROJECT_ID` |

> **Commit Message Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci` — following the [Conventional Commits](https://www.conventionalcommits.org/) specification.

> **Commit Scopes (examples):** `api`, `frontend`, `data`, `infra`, `auth`, `ci`, `arch`, `docs`. Scope is free-form but should match the affected system area. The scope `arch` is valid for architecture documentation changes.

> **Branch description:** The description after the type prefix (`feature/`, `fix/`, etc.) is free-form kebab-case. For example, `feature/v2-architecture` is valid under `feature/` — no separate `architecture/` branch type is needed.

---

### 19.6 Agent & Script Naming

| Element | Convention | Example |
| :--- | :--- | :--- |
| **Agent Slash Command** | `/<kebab-case>` | `/feature-development`, `/data-pipeline-evolution` |
| **Shell Script** | `<verb>_<noun>.sh` | `cost_sentinel.sh`, `get_diff.sh`, `check_links.sh` |
| **Python Script** | `<verb>_<noun>.py` | `validate_structure.py`, `generate_looker_spec.py` |
| **Agent SKILL file** | `SKILL.md` (uppercase, fixed filename) | `.agent/skills/backend-dev/SKILL.md` |
| **SKILL.md `name` field** | `kebab-case` | `backend-dev`, `data-engineer`, `bi-analyst` |

> **SKILL.md file naming disambiguation:** The agent configuration file is always named `SKILL.md` (all-caps). This is intentional — the uppercase filename signals that it is an agent-loaded configuration artifact, not a generic markdown document. The `kebab-case` convention in the row above applies exclusively to the `name:` field in the YAML front-matter of each `SKILL.md`, not the filename itself.

---

*Section added: 2026-02-23. Last updated: 2026-02-24. Owner: @architect.*