# Schema Reference — All Tables

← Part of [ARCHITECTURE.md](../ARCHITECTURE.md) | See also: [DATA_PIPELINE.md](DATA_PIPELINE.md) · [API.md](API.md) · [REPORTING.md](REPORTING.md)

---

## 13. Schema Reference — All Tables
Bronze Layer — victory_bronze
victory_bronze.raw_form_submissions
```sql
submission_id       STRING     NOT NULL  -- UUID, primary key
google_uid          STRING               -- Firebase Auth UID
submitted_at        TIMESTAMP  NOT NULL  -- Server-side timestamp
raw_payload         JSON       NOT NULL  -- Full form submission as JSON
source_page         STRING               -- Which page submitted (leader, event, profile, etc.)
ip_hash             STRING               -- SHA-256 hash of submitter IP (privacy-safe)
ingestion_timestamp TIMESTAMP  NOT NULL  -- Server-set BigQuery ingestion time. Used for table partitioning.
```
victory_bronze.raw_event_actions
```sql
action_id           STRING     NOT NULL  -- UUID, primary key
action_type         STRING     NOT NULL  -- created|registered|attended|cancelled
performed_by        STRING     NOT NULL  -- FK → victory_silver.persons.person_id. Semantics by action_type:
                                         --   created:    admin who created the event
                                         --   registered: the registrant's own person_id (self-reg) OR the admin's person_id (admin-reg)
                                         --   attended:   admin who marked attendance
                                         --   cancelled:  admin or the registrant who cancelled
performed_at        TIMESTAMP  NOT NULL  -- Server-side timestamp
payload             JSON                 -- Action-specific data
event_id            STRING               -- FK → victory_silver.events.event_id
ingestion_timestamp TIMESTAMP  NOT NULL  -- Server-set BigQuery ingestion time. Used for table partitioning.
```
victory_bronze.raw_headcounts
```sql
headcount_id        STRING     NOT NULL  -- UUID, primary key
date                DATE       NOT NULL  -- Date of the headcount
event_type          STRING     NOT NULL  -- e.g. "sunday_service", or the event category
event_id            STRING               -- FK → victory_silver.events.event_id (NULL for Sunday Service headcounts)
attendee_count      INT64      NOT NULL  -- Anonymous total; no per-person records
submitted_by        STRING     NOT NULL  -- FK → victory_silver.persons.person_id (admin)
submitted_at        TIMESTAMP  NOT NULL  -- Server-side timestamp
ingestion_timestamp TIMESTAMP  NOT NULL  -- Server-set BigQuery ingestion time. Used for table partitioning.
```

Silver Layer — victory_silver
victory_silver.persons (SCD2 — core table)
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

-- Contact (core — additional contacts via victory_silver.person_contacts)
email                       STRING               -- Firebase Auth email. Retained here for auth-email matching when admin-created records claim their Google account on first sign-in (Decision Log 2026-02-24). Canonical contact store is victory_silver.person_contacts.
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

victory_silver.person_contacts (SCD2)
```sql
contact_id      STRING     NOT NULL  -- UUID
person_id       STRING     NOT NULL  -- FK → victory_silver.persons
contact_type    STRING     NOT NULL  -- mobile|home|work|email|facebook|instagram
contact_value   STRING     NOT NULL
valid_from      TIMESTAMP  NOT NULL
valid_to        TIMESTAMP            -- NULL = current record
is_current      BOOL       NOT NULL  DEFAULT TRUE
```
victory_silver.person_occupations (SCD2)
```sql
occupation_id       STRING     NOT NULL  -- UUID
person_id           STRING     NOT NULL  -- FK → victory_silver.persons
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

victory_silver.person_roles (admin-managed)
```sql
role_id         STRING     NOT NULL  -- UUID
person_id       STRING     NOT NULL  -- FK → victory_silver.persons
role            STRING     NOT NULL  -- admin|executive|vg_leader|vg_member
assigned_by     STRING     NOT NULL  -- FK → victory_silver.persons (admin)
assigned_at     TIMESTAMP  NOT NULL
is_active       BOOL       NOT NULL  DEFAULT TRUE
```
victory_silver.equipping_classes
```sql
class_id                STRING     NOT NULL  -- UUID
canonical_step          STRING     NOT NULL  -- victory_weekend|discipleship_class|
                                             -- spiritual_foundations|leadership_113
class_name              STRING     NOT NULL  -- e.g. "Spiritual Foundations Batch 12"
batch_code              STRING               -- e.g. "SF-2025-B12"
facilitator_person_id   STRING               -- FK → victory_silver.persons
start_date              DATE       NOT NULL
end_date                DATE
capacity                INT64
status                  STRING     NOT NULL  -- upcoming|ongoing|completed|cancelled
created_by              STRING               -- FK → victory_silver.persons (admin)
created_at              TIMESTAMP  NOT NULL
```
victory_silver.equipping_enrollments
```sql
enrollment_id           STRING     NOT NULL  -- UUID
class_id                STRING     NOT NULL  -- FK → victory_silver.equipping_classes
person_id               STRING     NOT NULL  -- FK → victory_silver.persons
step_name_as_completed  STRING               -- Exact name on certificate (preserves "Leader's Lab")
enrollment_status       STRING     NOT NULL  -- enrolled|completed|dropped
enrolled_at             TIMESTAMP  NOT NULL
completed_at            TIMESTAMP            -- NULL until completed
dropped_at              TIMESTAMP            -- NULL unless dropped
drop_reason             STRING
notes                   STRING
created_by              STRING               -- FK → victory_silver.persons (admin)
created_at              TIMESTAMP  NOT NULL
```
victory_silver.event_type_catalog (admin-managed)
```sql
event_type_id   STRING   NOT NULL  -- UUID
type_name       STRING   NOT NULL  -- e.g. "Date Talk"
category        STRING   NOT NULL  -- equipping|event|pastoral_self|pastoral_admin|...
equipping_step  STRING             -- Canonical step name or NULL
is_paid         BOOL     NOT NULL  DEFAULT FALSE
default_price   NUMERIC
currency        STRING             -- "PHP"
```
victory_silver.events (admin-managed)
```sql
event_id          STRING     NOT NULL  -- UUID
event_type_id     STRING     NOT NULL  -- FK → victory_silver.event_type_catalog
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
created_by        STRING               -- FK → victory_silver.persons (admin)
created_at        TIMESTAMP  NOT NULL
```
victory_silver.event_registrations (self-register + admin)
```sql
registration_id       STRING     NOT NULL  -- UUID (deterministic hash of event_id + person_id for self-reg)
event_id              STRING     NOT NULL  -- FK → victory_silver.events
person_id             STRING               -- FK → victory_silver.persons (NULL if no account yet)
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

victory_silver.event_attendances (admin check-in)
```sql
attendance_id       STRING     NOT NULL  -- UUID
event_id            STRING     NOT NULL  -- FK → victory_silver.events
person_id           STRING     NOT NULL  -- FK → victory_silver.persons
registration_id     STRING               -- FK → victory_silver.event_registrations (if pre-registered)
checked_in_at       TIMESTAMP  NOT NULL
check_in_method     STRING     NOT NULL  -- manual|qr_scan
checked_in_by       STRING               -- FK → victory_silver.persons (admin)
session_tag         STRING               -- e.g. "morning" / "afternoon" for multi-session events
```
victory_silver.victory_groups (SCD2)
```sql
group_id              STRING     NOT NULL  -- UUID
leader_person_id      STRING     NOT NULL  -- FK → victory_silver.persons
group_name            STRING
group_type            STRING               -- single|wives|husbands|students|young_pro
is_active             BOOL       NOT NULL  DEFAULT TRUE
valid_from            TIMESTAMP  NOT NULL
valid_to              TIMESTAMP            -- NULL = current record
is_current            BOOL       NOT NULL  DEFAULT TRUE
```
victory_silver.victory_group_members
```sql
membership_id         STRING     NOT NULL  -- UUID
group_id              STRING     NOT NULL  -- FK → victory_silver.victory_groups
person_id             STRING               -- FK → victory_silver.persons (NULL if member not yet in system)
member_first_name     STRING     NOT NULL  -- Captured from leader form
member_last_name      STRING     NOT NULL  -- Captured from leader form
is_active             BOOL       NOT NULL  DEFAULT TRUE
added_at              TIMESTAMP  NOT NULL
removed_at            TIMESTAMP            -- NULL = currently active
```

**Linking strategy:** `person_id` is NULL when the VG member has not yet been registered in the system. This allows leaders to submit member names immediately without requiring every member to have a system account first.

**Admin linking procedure:** The admin portal surfaces unlinked members (where `person_id IS NULL`) in a dedicated "Unlinked VG Members" queue accessible from `/admin`. For each unlinked member, the admin can:
1. **Search for existing person** — Admin types the member's name; system calls `GET /api/persons?q=<name>` to search `victory_silver.persons`.
2. **Link** — Admin selects the matching person; calls `PATCH /api/vg-members/{membership_id}/link` with `{ "person_id": "<uuid>" }` (admin role required).
3. **Create new person** — If no match found, admin creates a new Contact-stage record; system auto-links after creation.
4. **Leave unlinked** — Admin can dismiss; `person_id` remains NULL and member name is captured but not linked.

victory_silver.intern_relationships
```sql
relationship_id     STRING     NOT NULL  -- UUID, primary key
intern_person_id    STRING               -- FK → victory_silver.persons. NULLABLE. NULL when the name typed by
                                         -- the VG Leader in Section 3 could not be auto-matched to a
                                         -- unique victory_silver.persons record. Admin must link via
                                         -- PATCH /api/intern-relationships/{id}/link before approving.
intern_first_name   STRING     NOT NULL  -- First name as typed by the VG Leader on form submission.
                                         -- Preserved as audit trail regardless of resolution status.
intern_last_name    STRING     NOT NULL  -- Last name as typed by the VG Leader on form submission.
leader_person_id    STRING     NOT NULL  -- FK → victory_silver.persons (the supervising VG Leader — must be a registered person)
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

**Relationship note:** This table is the canonical FK for the intern-leader data relationship. `leader_person_id` must be a registered `victory_silver.persons` record. `intern_person_id` is nullable — it is resolved from the name typed by the VG Leader via auto-match or admin linking. A record with `intern_person_id = NULL` is considered unresolved and cannot be approved. The `vg_leader_first_name/last_name` on `victory_silver.persons` serves as a display cache derived from this relationship by the Silver pipeline — only from records where `review_status = 'approved'` and `intern_person_id IS NOT NULL`. If multiple approved active records exist for the same intern, the most recent `start_date` is used. See Stage 03 and Decision Log 2026-02-24.

**Lifecycle management:**
- **Creation:** Dataform `stg_intern_relationships.sqlx` INSERTs a new `pending` record whenever a VG Leader names an intern in Section 3 of their form submission. Admin also creates records directly via `POST /api/intern-relationships` (admin-created, auto-approved).
- **Approval:** Admin sets `review_status = 'approved'` via `PATCH /api/intern-relationships/{id}`. The Silver pipeline syncs the `vg_leader_first_name/last_name` display cache on the intern's `victory_silver.persons` record on the next scheduled run.
- **Duplicate pending records:** If the same intern is named across multiple leader form resubmissions, each generates a new `pending` record. Admin reviews the queue and rejects duplicates — only one `approved` record per active intern-leader pair should exist.
- **Closure (intern → leader promotion):** When an intern is promoted to VG Leader, admin must set `is_active = FALSE` and `end_date = today` via `PATCH /api/intern-relationships/{id}`. This is step 5 of the Stage 04 entry process. Without this, the former intern remains in active intern counts and in the supervising leader's form pre-fill indefinitely.
victory_silver.ministry_catalog + victory_silver.ministry_memberships
```sql
-- ministry_catalog
ministry_id      STRING  NOT NULL  -- UUID
ministry_name    STRING  NOT NULL
category         STRING             -- music|media|kids|ushering|prayer|...

-- ministry_memberships
membership_id    STRING     NOT NULL  -- UUID
ministry_id      STRING     NOT NULL  -- FK → victory_silver.ministry_catalog
person_id        STRING     NOT NULL  -- FK → victory_silver.persons
status           STRING     NOT NULL  -- interested|active|inactive
joined_at        TIMESTAMP
```
victory_silver.person_relationships (Phase 2)
```sql
person_id_a           STRING  NOT NULL  -- FK → victory_silver.persons
person_id_b           STRING  NOT NULL  -- FK → victory_silver.persons
relationship_type     STRING  NOT NULL  -- spouse|parent_child|referred_by
```
victory_silver.headcounts (admin-managed)
```sql
headcount_id    STRING     NOT NULL  -- UUID, primary key
date            DATE       NOT NULL  -- Date of the headcount
event_type      STRING     NOT NULL  -- e.g. "sunday_service", or the event category
event_id        STRING               -- FK → victory_silver.events.event_id (NULL for Sunday Service headcounts)
attendee_count  INT64      NOT NULL  -- Anonymous total; no per-person records
submitted_by    STRING     NOT NULL  -- FK → victory_silver.persons.person_id (admin)
submitted_at    TIMESTAMP  NOT NULL
```

victory_silver.data_change_log (audit)
```sql
log_id       STRING     NOT NULL  -- UUID
table_name   STRING     NOT NULL
record_id    STRING     NOT NULL
changed_by   STRING     NOT NULL  -- FK → victory_silver.persons (admin)
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


---

*Owner: @architect. Last updated: 2026-02-24.*
