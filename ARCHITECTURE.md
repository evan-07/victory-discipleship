# Victory Church — Master Architecture Plan

**Version:** 4.0 (Refined)
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
- [Naming Conventions & Consistency Standards](#20-naming-conventions--consistency-standards)


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
| Facebook Profile | silver.person_contacts (type: facebook) | URL or profile name |

### Stage 02 — Member

- **Definition:** Completed One2One, part of the movement. Consumer stage.
- **Entry point:** Admin records `one2one_completed = true` and `one2one_date`. Sets `journey_stage = member`.
- **Characteristics:** Part of a Victory Group as a member. Attends events and services.
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
- **Entry point:** Admin sets `journey_stage = intern` and the VG Leader records them as an intern on the leader form.
- **Characteristics:** Active intern under a VG Leader. Listed in `silver.intern_relationships` linked to their supervising leader.
- **Next step:** Lead their own group → becomes a VG Leader.

**Required fields:** Same as Member. The intern is still under a VG Leader and has the same data requirements. The `intern_relationships` table records their supervising leader separately from the `vg_leader_first_name` / `vg_leader_last_name` fields.

### Stage 04 — VG Leader

- **Definition:** Leading their own Victory Group(s).
- **Entry point:** Submitted the VG Leader form → admin reviewed → admin assigned `vg_leader` role → `journey_stage = leader`.
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
| Facebook Profile | ✅ | ✅ | ✅ | ✅ |
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
| `source` | STRING | form_submission · event_registration · bulk_import · admin_created · pastoral_event |
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
| `/profile.html` | VG Members | Google Sign-In | Phase 2: own record view and edit |
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
| `GET/PATCH /api/persons` | GET, PATCH | admin | Admin CRUD for person records |
| `GET /api/events` | GET | admin, executive | List all events |
| `POST /api/events` | POST | admin | Create new event instance |
| `GET /api/events/{slug}/pre-check` | GET | authenticated | Pre-registration check: person exists, profile completeness, duplicate registration check, upcoming event list |
| `POST /api/events/{slug}/self-register` | POST | authenticated | Self-register for a public event. Returns 409 if already registered. |
| `POST /api/events/{id}/register` | POST | admin | Admin registers a person for an event |
| `POST /api/events/{id}/attend` | POST | admin | Mark attendance (triggers discipleship pipeline) |
| `POST /api/headcounts` | POST | admin | Submit anonymous headcount for an event or Sunday Service |
| `GET /api/leaders/me` | GET | `vg_leader` | VG Leader's own profile, groups, and member list |
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
2. Query `silver.persons` for matching `google_uid` (WHERE `is_current = TRUE`).
3. If person found → query `silver.event_registrations` for this event + person (WHERE `status != 'cancelled'`).
4. If person found → query `silver.event_registrations` for ALL upcoming events (WHERE `event.start_datetime > NOW()` AND `status IN ('registered')`).
5. Compute `profile_complete` based on contact-stage required fields being non-NULL.
6. Return assembled response.

### Duplicate Registration Prevention (`POST /api/events/{slug}/self-register`)

```python
# Pseudocode for self-register endpoint
def self_register(slug, jwt_user):
    person = lookup_person(jwt_user.google_uid)
    event = lookup_event(slug)

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

### Discipleship Auto-Pipeline (Event Attendance → Enrollment Record)

Copy
```plaintext
1. Admin POSTs to /api/events/{id}/attend with person_id
2. Cloud Run writes attendance to bronze.raw_event_actions (immediate, streaming)
3. Cloud Run writes to silver.event_attendances
4. Cloud Run fetches event_type from silver.event_type_catalog
5. If event_type.equipping_step IS NOT NULL → upsert silver.equipping_enrollments
6. Cloud Run publishes a Pub/Sub message for async Dataform refresh trigger
7. Gold views update automatically — Looker Studio reflects the change on next data refresh
```

### Primary Terraform Resources

| Resource | Service | Purpose |
| :--- | :--- | :--- |
| `google_cloud_run_service` | Cloud Run | Hosts FastAPI backend API |
| `google_bigquery_dataset` | BigQuery | Bronze, Silver, Gold datasets |
| `google_dataform_repository` | Dataform | SQL pipeline automation |
| `google_pubsub_topic` | Pub/Sub | Event trigger for immediate data refresh |
| `google_secret_manager_secret` | Secret Manager | Store API keys & Service Account JSON |
| `cloudflare_pages_project` | Cloudflare | Static frontend hosting |
| `google_service_account` | IAM | Least-privileged identity for Cloud Run |

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
📝 VG Leader Form   🎉 Event Registration   📦 Bulk Import   🔧 Admin Direct Entry
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
│  raw_bulk_imports · raw_headcounts                        │
└──────────────────────────────────────────────────────────┘
                              │
                    Dataform — SCD2 upsert
                    dedup by email + google_uid
                    Every 15 min + Pub/Sub trigger
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

- **Cloud Scheduler:** Dataform workflow run every 15 minutes for routine Silver updates.
- **Pub/Sub:** Immediate Dataform run when Cloud Run publishes an attendance event (near-real-time discipleship updates).

### Transformation Graph

| SQLX File | Source | Target | Trigger |
| :--- | :--- | :--- | :--- |
| `stg_persons.sqlx` | `bronze.raw_form_submissions` | `silver.persons` (SCD2 upsert) | Scheduled (15 min) |
| `stg_contacts.sqlx` | `bronze.raw_form_submissions` | `silver.person_contacts` | Scheduled (15 min) |
| `stg_occupations.sqlx` | `bronze.raw_form_submissions` | `silver.person_occupations` | Scheduled (15 min) |
| `stg_victory_groups.sqlx` | `bronze.raw_form_submissions` | `silver.victory_groups` | Scheduled (15 min) |
| `stg_vg_members.sqlx` | `bronze.raw_form_submissions` | `silver.victory_group_members` | Scheduled (15 min) |
| `stg_events.sqlx` | `bronze.raw_event_actions` | `silver.events` + `silver.event_type_catalog` | Scheduled (15 min) |
| `stg_registrations.sqlx` | `bronze.raw_event_actions` | `silver.event_registrations` | Scheduled (15 min) |
| `stg_attendances.sqlx` | `bronze.raw_event_actions` | `silver.event_attendances` | Pub/Sub (immediate) |
| `stg_headcounts.sqlx` | `bronze.raw_headcounts` | `silver.headcounts` | Scheduled (15 min) |
| `discipleship_pipeline.sqlx` | `silver.event_attendances` + `silver.event_type_catalog` | `silver.equipping_enrollments` | Pub/Sub (immediate) |
| `gold_demographics.sqlx` | `silver.persons` | `gold.vw_member_demographics` | On silver table update |
| `gold_events.sqlx` | `silver.events` + `silver.event_attendances` | `gold.vw_event_participation` | On silver table update |
| `gold_headcounts.sqlx` | `silver.headcounts` + `silver.events` | `gold.vw_attendance_headcounts` | On silver table update |
| `gold_funnel.sqlx` | `silver.equipping_enrollments` + `silver.events` | `gold.vw_equipping_funnel` | On silver table update |
| `gold_vg_summary.sqlx` | `silver.victory_groups` + `silver.victory_group_members` | `gold.vw_victory_group_summary` | On silver table update |
| `gold_engagement.sqlx` | `silver.event_attendances` + `silver.event_registrations` | `gold.vw_person_engagement` | On silver table update |
| `gold_event_history.sqlx` | `silver.event_attendances` + `silver.event_registrations` + `silver.events` + `silver.equipping_enrollments` | `gold.vw_person_event_history` | On silver table update |
| `gold_equipping_completion.sqlx` | `silver.equipping_enrollments` + `silver.persons` | `gold.vw_equipping_completion` | On silver table update |
| `gold_equipping_cohorts.sqlx` | `silver.equipping_classes` + `silver.equipping_enrollments` | `gold.vw_equipping_cohorts` | On silver table update |
| `gold_leader_dashboard.sqlx` | `silver.victory_groups` + `silver.victory_group_members` + `silver.equipping_enrollments` + `silver.event_attendances` + `silver.ministry_memberships` | `gold.vw_leader_dashboard` | On silver table update |
| `gold_ministry_participation.sqlx` | `silver.ministry_memberships` + `silver.ministry_catalog` | `gold.vw_ministry_participation` | On silver table update |
| `gold_pastoral_events.sqlx` | `silver.events` + `silver.event_registrations` + `silver.persons` | `gold.vw_pastoral_events` | On silver table update |
| `gold_admin_full.sqlx` | `silver.persons` + `silver.person_occupations` + `silver.person_contacts` + `silver.equipping_enrollments` + `silver.victory_groups` + `silver.ministry_memberships` | `gold.vw_admin_full` | On silver table update |
| `gold_business_network.sqlx` | `silver.persons` + `silver.person_occupations` | `gold.vw_business_network` | On silver table update |

**Dataform assertions:** Each `.sqlx` file includes assertions that verify data quality before writing to the next layer (e.g. `assert person_id IS NOT NULL`, `assert email matches regex pattern`). A failing assertion stops the pipeline and sends an alert — bad data never reaches Gold.


## 9. Data Flow Diagram

### Data Entry Sources

Copy
```plaintext
VG Leader Form       Event Registration    Bulk Import (CSV)    Admin Direct Entry
/leader              /e/[slug]             Admin portal          Create Profile tool
Google Sign-In       Google Sign-In        Data migration        Event / Class mgmt
       │                    │                    │                      │
       └────────────────────┴────────────────────┴──────────────────────┘
                                         │
                        All sources write to Bronze first
                        via Cloud Run API (streaming insert)
```

### Bronze Tables

Copy
```plaintext
bronze.raw_form_submissions        bronze.raw_event_actions         bronze.raw_bulk_imports         bronze.raw_headcounts
───────────────────────────        ─────────────────────────        ──────────────────────────      ───────────────────────
submission_id    UUID              action_id        UUID            import_id       UUID            headcount_id  UUID
google_uid       STRING            action_type      STRING          imported_by     FK person_id    date          DATE
submitted_at     TIMESTAMP         performed_by     FK person_id    imported_at     TIMESTAMP       event_type    STRING
raw_payload      JSON              payload          JSON            row_count       INT64           event_id      FK / NULL
source_page      STRING            event_id         FK              raw_csv_payload JSON array      attendee_count INT64
ip_hash          STRING                                             error_rows      JSON array      submitted_by  FK person_id
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
email · phone · address                   nature_of_business · business_name
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
│   ├── definitions/         # .sqlx files (Bronze -> Silver -> Gold)
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
- **Backend:** On push to `main` → Build Docker image → Push to Artifact Registry → Deploy to Cloud Run.
- **Dataform:** On push to `main` → Compile Dataform → Test assertions → Deploy to Dataform service.
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
  └── Docker container registry for Cloud Run images

Secret Manager
  └── Secret placeholders (values set manually or via CI)

Cloud Scheduler
  └── Dataform trigger jobs (every 15 minutes)

Pub/Sub
  └── Topics and subscriptions (attendance → equipping pipeline)

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
### Cloudflare Access (Admin Gate)

The /admin and /events pages are additionally protected by Cloudflare Access (free for up to 50 users). This adds a zero-trust authentication layer at the CDN edge — before the page even loads. Only email addresses in the approved list can access these paths. A valid Firebase Auth token is then also required to make any API calls.
### Principle of Least Privilege — IAM Roles

| Service Account | BigQuery Role | Other Roles |
| :--- | :--- | :--- |
| Cloud Run (backend) | `bigquery.dataEditor` on `silver` only | `secretmanager.secretAccessor`, `pubsub.publisher` |
| Dataform | `bigquery.dataEditor` on `silver` + `gold`; `bigquery.dataViewer` on `bronze` | None additional |
| Looker Studio | `bigquery.dataViewer` on `gold` dataset only | None additional |
| GitHub Actions (deploy) | None (Terraform manages BigQuery) | `run.admin`, `artifactregistry.writer`, `iam.serviceAccountUser` |
| GitHub Actions (Terraform) | `bigquery.admin` (for schema management only) | `resourcemanager.projectIamAdmin` (scoped) |

## 12. UX Flows
### Entry Points Summary

| Entry Point | URL | Who | Auth | Key Behavior | Phase |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Event Landing Page | `/e/[slug]` | Anyone | Google Sign-In | Smart pre-check → profile form or confirm or already-registered screen. VG question for new users. | Phase 1 |
| VG Leader Form | `/leader` | VG Leaders | Google Sign-In | New → blank form. Returning → full pre-fill. Captures personal info + groups + members. | Phase 1 |
| Admin Portal | `/admin` | Admin team | Google Sign-In + admin role | Review queue, event management, class roster management, person editing, role assignment, bulk import. | Phase 1 |
| Reports | `/reports` | Executives | Google Sign-In + executive role | Embedded Looker Studio dashboards. No data editing. | Phase 1 |
| Member Profile | `/profile` | VG Members | Google Sign-In | View and update own record. Cannot see other records. | Phase 2 |
| Pastoral Event Page | `/e/[slug]` | Families / couples | Google Sign-In | Simplified form capturing person being celebrated as primary record. | Phase 1 |

### VG Leader Form — Returning User Flow

Copy
```plaintext
1. Leader opens /leader → Google Sign-In (one-tap if already signed in)
2. Frontend calls GET /api/me with JWT
3. Cloud Run looks up record by google_uid → returns full profile + groups + members
4. Form pre-fills:
   Section 1 — Personal Info (all Member/Intern fields)
   Section 2 — Groups Led (one card per group, type + member list)
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
│          [ Submit ]                     │
└─────────────────────────────────────────┘
```

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
6. Backend: creates person record (bronze + silver) + creates event registration
7. SUCCESS SCREEN (clean confirmation — no payment instructions)
```

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
6. Backend: updates person profile + auto-creates registration (no re-register needed)
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

Every record created by a public form or bulk import starts as `review_status = 'pending'`. The admin portal surfaces these records in a dedicated view.

Copy
```plaintext
┌──────────────────────────────────────────────────────────┐
│  PENDING RECORDS REVIEW QUEUE                            │
│  ──────────────────────────────────────────────────────  │
│  [ Juan Dela Cruz ]   Source: Event   Duplicate: YES (72%)│
│  [ Review ] [ Merge with 0001 ] [ Discard ]             │
│                                                          │
│  [ Maria Clara ]      Source: Form    Duplicate: NO       │
│  [ Approve ] [ Reject ] [ Edit ]                         │
└──────────────────────────────────────────────────────────┘
```

### Event Payment Flow

Copy
```plaintext
1. Person registers online → status = 'registered', paid = FALSE
2. Success message includes payment instructions (GCash/Bank/Physical)
3. Person pays externally
4. Person brings receipt to physical counter OR sends to admin email
5. Admin looks up person in /events portal → clicks [ Mark Paid ] → enters Reference #
6. Status remains 'registered' but paid column = TRUE
7. Upon arrival at event venue: Admin clicks [ Attend ]
8. Status → 'attended'. Discipleship pipeline triggers enrollment if applicable.
```

No payment gateway in Phase 1. All payment confirmation is manual. Payment instructions are never displayed on the registration success screen.


## 13. Schema Reference — All Tables
Bronze Layer — victory_bronze
bronze.raw_form_submissions
```sql
submission_id   STRING     NOT NULL  -- UUID, primary key
google_uid      STRING               -- Firebase Auth UID
submitted_at    TIMESTAMP  NOT NULL  -- Server-side timestamp
raw_payload     JSON       NOT NULL  -- Full form submission as JSON
source_page     STRING               -- Which page submitted (leader, event, profile, etc.)
ip_hash         STRING               -- SHA-256 hash of submitter IP (privacy-safe)
```
bronze.raw_event_actions
```sql
action_id       STRING     NOT NULL  -- UUID, primary key
action_type     STRING     NOT NULL  -- created|registered|attended|cancelled
performed_by    STRING     NOT NULL  -- FK → silver.persons.person_id
performed_at    TIMESTAMP  NOT NULL  -- Server-side timestamp
payload         JSON                 -- Action-specific data
event_id        STRING               -- FK → silver.events.event_id
```
bronze.raw_bulk_imports
```sql
import_id           STRING     NOT NULL  -- UUID, primary key
imported_by         STRING     NOT NULL  -- FK → silver.persons.person_id (admin)
imported_at         TIMESTAMP  NOT NULL  -- Server-side timestamp
row_count           INT64      NOT NULL  -- Total rows in CSV
raw_csv_payload     JSON       NOT NULL  -- Full CSV as JSON array
error_rows          JSON                 -- Rows that failed validation
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

-- Contact (core — additional via person_contacts)
email                       STRING
phone                       STRING
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
source                      STRING               -- form_submission|event_registration|bulk_import|admin_created|pastoral_event
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
silver.person_contacts (SCD2)
```sql
contact_id      STRING     NOT NULL  -- UUID
person_id       STRING     NOT NULL  -- FK → silver.persons
contact_type    STRING     NOT NULL  -- mobile|home|work|email|facebook|instagram
contact_value   STRING     NOT NULL
valid_from      TIMESTAMP
valid_to        TIMESTAMP
is_current      BOOL
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
type_id         STRING   NOT NULL  -- UUID
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
check_in_method     STRING     NOT NULL  -- manual|bulk_import|qr_scan
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
valid_from            TIMESTAMP
valid_to              TIMESTAMP
is_current            BOOL
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

Linking strategy: person_id is NULL when the VG member has not yet been registered in the system. When a matching person record is found (via name + other identifiers), admin can link the records. This allows leaders to submit member names immediately without requiring every member to have a system account first.

silver.intern_relationships
```sql
intern_person_id    STRING     NOT NULL  -- FK → silver.persons
leader_person_id    STRING     NOT NULL  -- FK → silver.persons
start_date          DATE       NOT NULL
end_date            DATE                 -- NULL = currently active
is_active           BOOL       NOT NULL  DEFAULT TRUE
```
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
| `victory_bronze` | `raw_bulk_imports` | Append-only | Phase 1 |
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
| **Phase 1** | **Foundations & Core CRM** | Monorepo setup, Cloud Run container, BigQuery Bronze/Silver, Dataform pipeline, VG Leader Form (HTML/Alpine.js), Admin Review Queue, Google Sign-In, Role-based access. |
| **Phase 2** | **Event Management** | Event Type Catalog, Public Landing Pages (`/e/[slug]`), Self-registration logic, Duplicate checking, Admin Event Management UI, Attendance tracking. |
| **Phase 3** | **Discipleship Pipeline** | Equipping class cohorts, Enrollment logic, Discipleship milestones (SF, LW, LF), Looker Studio executives dashboards, Discipleship pipeline drill-downs. |
| **Phase 4** | **Automation & Scale** | Bulk import tool, Person merging logic, Audit logging (SCD2 data_change_log), Advanced engagement scoring (recency/frequency), Performance tuning. |
| **Phase 5** | **Member Self-Service** | `/profile` page for members to view results, digital badge collection, event history, ministry involvement summary. |

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
| 2025-01-30 | Event attendance for large events | Phase 1: one-by-one check-in in admin UI. Phase 2: bulk CSV upload. Same schema supports both — no changes needed when bulk ships. | ✅ Final |
| 2025-01-31 | Person relationships (couples, parents) | Phase 2. Every person is an independent record in Phase 1. silver.person_relationships table added in Phase 2. | ✅ Final |
| 2025-02-01 | Existing data migration approach | Bulk CSV import for most records + admin "Create Profile" tool for stragglers. Migrated records claim their Google account on first sign-in by email match. | ✅ Final |
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

## 19. Appendix

- **Canva Integration:** No API needed. Just standard image uploads.
- **Reporting:** Looker Studio using BigQuery native connector. One Data Source per view in `victory_gold`.
- **Legacy Support:** Both old and new pathway steps are permanently valid and reportable.
- **Data Sovereignty:** All data strictly within GCP Philippines/Taiwan regions. No external SaaS (except Cloudflare edge).

No open questions remain. This document represents the complete agreed-upon design.
Next steps: Begin Phase 1 build — Terraform resource definitions → BigQuery dataset and table creation → FastAPI skeleton with pre-check and self-register endpoints → Cloudflare Pages deploy → Dataform pipeline implementation.



Victory Church · Master Architecture Plan · v4.0 · Confidential — Internal Use Only

---

## 20. Naming Conventions & Consistency Standards

This section is the **authoritative and binding** source for all naming conventions across the Victory Discipleship system. All agents, engineers, and contributors MUST follow these rules. Any deviation requires an `@architect` review and a documented decision in Section 18 (Decision Log).

> **Enforcement:** These rules are cross-checked by `validate_structure.py` and `schema_lint.py` during every CI/CD run.

---

### 20.1 Data Architecture (BigQuery & Dataform)

| Element | Convention | Example | Rule |
| :--- | :--- | :--- | :--- |
| **BigQuery Dataset — Bronze** | `1_bronze` | `victory_bronze` | Fixed. Never rename datasets. |
| **BigQuery Dataset — Silver** | `2_silver` | `victory_silver` | Fixed. Never rename datasets. |
| **BigQuery Dataset — Gold** | `3_gold` | `victory_gold` | Fixed. Never rename datasets. |
| **Bronze Table** | `raw_<entity_plural>` | `raw_form_submissions`, `raw_events` | All bronze tables start with `raw_`. |
| **Silver Table** | `<entity_plural>` | `persons`, `events`, `intern_relationships` | Plain, normalized plural nouns. |
| **Silver SQLX File** | `stg_<entity>.sqlx` | `stg_persons.sqlx`, `stg_events.sqlx` | `stg_` prefix distinguishes the transform file from the table it produces. |
| **Gold View** | `vw_<business_domain>` | `vw_member_demographics`, `vw_attendance_trends` | `vw_` prefix explicitly denotes a read-only BigQuery view. |
| **Gold Dimension Table** | `dim_<entity>` | `dim_members`, `dim_ministry_teams` | OLAP-style dimension prefix. |
| **Gold Fact Table** | `fact_<event>` | `fact_attendance`, `fact_event_registrations` | OLAP-style fact prefix. |
| **Gold Aggregate/Report** | `agg_<topic>` or `rpt_<topic>` | `agg_monthly_stats`, `rpt_leader_headcounts` | For pre-aggregated reporting tables. |

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

### 20.2 Backend (Python / FastAPI)

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

### 20.3 Frontend (HTML / CSS / JS)

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

### 20.4 Infrastructure (Terraform & GCP)

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

### 20.5 Git & CI/CD

| Element | Convention | Example |
| :--- | :--- | :--- |
| **Branch Name** | `<type>/<kebab-case-description>` | `feature/member-search`, `fix/dataform-bug` |
| **Branch Types** | `feature/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/` | See `README.md` Section 3 |
| **Commit Message** | `<type>(<scope>): <short description>` | `feat(api): add person export endpoint` |
| **GitHub Actions Workflow File** | `kebab-case.yaml` | `deploy-backend.yaml`, `sonarqube-analysis.yaml` |
| **GitHub Actions Secret** | `UPPER_SNAKE_CASE` | `WIF_PROVIDER`, `GCP_PROJECT_ID` |

> **Commit Message Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci` — following the [Conventional Commits](https://www.conventionalcommits.org/) specification.

---

### 20.6 Agent & Script Naming

| Element | Convention | Example |
| :--- | :--- | :--- |
| **Agent Slash Command** | `/<kebab-case>` | `/feature-development`, `/data-pipeline-evolution` |
| **Shell Script** | `<verb>_<noun>.sh` | `cost_sentinel.sh`, `get_diff.sh`, `check_links.sh` |
| **Python Script** | `<verb>_<noun>.py` | `validate_structure.py`, `generate_looker_spec.py` |
| **SKILL.md `name` field** | `kebab-case` | `backend-dev`, `data-engineer`, `bi-analyst` |

---

*Section added: 2026-02-23. Owner: @architect.*