# Data Architecture & Pipeline

← Part of [ARCHITECTURE.md](../ARCHITECTURE.md) | See also: [SCHEMA.md](SCHEMA.md) · [API.md](API.md) · [REPORTING.md](REPORTING.md)

---

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
| `stg_persons.sqlx` | `2_silver` | `victory_bronze.raw_form_submissions` | `victory_silver.persons` (SCD2 upsert) | Scheduled (hourly, Dataform native) — **MERGE key priority: (1) `google_uid` (non-NULL) — primary key; handles two-phase write reconciliation. (2) `person_id` — fallback for admin-created records where `google_uid IS NULL`. Two-phase write behavior: if a Bronze `source_page = 'event_registration'` record's `google_uid` matches an existing `is_current = TRUE` Silver row, Dataform SCD2 closes that row and inserts a fully-populated new row — carrying forward the original `person_id` (preserving FK integrity on `event_registrations`). A new `person_id` is never assigned during reconciliation.** Assertions: (a) `assert_single_active_per_google_uid` — detects google_uid collision (Priority 0 duplicate signal); (b) `assert_google_uid_uniqueness` — halts pipeline if two `is_current = TRUE` rows share the same non-NULL `google_uid` and sets `duplicate_flag = TRUE` on both. |
| `stg_contacts.sqlx` | `2_silver` | `victory_bronze.raw_form_submissions` | `victory_silver.person_contacts` | Scheduled (hourly, Dataform native) |
| `stg_occupations.sqlx` | `2_silver` | `victory_bronze.raw_form_submissions` | `victory_silver.person_occupations` | Scheduled (hourly, Dataform native) |
| `stg_victory_groups.sqlx` | `2_silver` | `victory_bronze.raw_form_submissions` | `victory_silver.victory_groups` | Scheduled (hourly, Dataform native) |
| `stg_vg_members.sqlx` | `2_silver` | `victory_bronze.raw_form_submissions` | `victory_silver.victory_group_members` | Scheduled (hourly, Dataform native) |
| `stg_intern_relationships.sqlx` | `2_silver` | `victory_bronze.raw_form_submissions` | `victory_silver.intern_relationships` — INSERTs a new `pending` record for each intern named in Section 3 of a leader form submission, **unless** an `approved`, `is_active = TRUE` record already exists for the same `leader_person_id` + `intern_first_name` + `intern_last_name` combination (de-duplication rule — skips insert for already-confirmed interns on re-submission). Auto-match: case-insensitive exact match of the typed intern first + last name against `victory_silver.persons` (WHERE `is_current = TRUE`): if exactly one match, `intern_person_id` is populated; if zero or multiple matches, `intern_person_id` is set to NULL and the record appears in the admin "Unresolved Interns" queue (Tab 3). `intern_first_name` and `intern_last_name` are always stored as typed. | Scheduled (hourly, Dataform native) |
| `stg_events.sqlx` | `2_silver` | `victory_bronze.raw_event_actions` (action_type = 'created') | `victory_silver.events` | Scheduled (hourly, Dataform native) |
| `stg_registrations.sqlx` | `2_silver` | `victory_bronze.raw_event_actions` (action_type = 'registered') | `victory_silver.event_registrations` | Scheduled (hourly, Dataform native) |
| `stg_attendances.sqlx` | `2_silver` | `victory_bronze.raw_event_actions` (action_type = 'attended') | `victory_silver.event_attendances` | Pub/Sub (immediate, via Cloud Function) |
| `stg_headcounts.sqlx` | `2_silver` | `victory_bronze.raw_headcounts` | `victory_silver.headcounts` | Scheduled (hourly, Dataform native) |
| `discipleship_pipeline.sqlx` | `2_silver` | `victory_silver.event_attendances` + `victory_silver.event_type_catalog` + `victory_silver.equipping_enrollments` + `victory_silver.equipping_classes` | `victory_silver.equipping_enrollments` — UPDATES existing `enrolled` records to `completed`. Never creates new enrollment records. No-op when `equipping_step IS NULL`. | Pub/Sub (immediate, via Cloud Function) |
| `gold_demographics.sqlx` | `3_gold` | `victory_silver.persons` | `victory_gold.vw_member_demographics` | Scheduled (hourly, Dataform native) |
| `gold_events.sqlx` | `3_gold` | `victory_silver.events` + `victory_silver.event_attendances` | `victory_gold.vw_event_participation` | Scheduled (hourly, Dataform native) |
| `gold_headcounts.sqlx` | `3_gold` | `victory_silver.headcounts` + `victory_silver.events` | `victory_gold.vw_attendance_headcounts` | Scheduled (hourly, Dataform native) |
| `gold_funnel.sqlx` | `3_gold` | `victory_silver.equipping_enrollments` + `victory_silver.equipping_classes` + `victory_silver.persons` | `victory_gold.vw_equipping_funnel` | Scheduled (hourly, Dataform native) |
| `gold_vg_summary.sqlx` | `3_gold` | `victory_silver.victory_groups` + `victory_silver.victory_group_members` | `victory_gold.vw_victory_group_summary` | Scheduled (hourly, Dataform native) |
| `gold_engagement.sqlx` | `3_gold` | `victory_silver.event_attendances` + `victory_silver.event_registrations` | `victory_gold.vw_person_engagement` | Scheduled (hourly, Dataform native) |
| `gold_event_history.sqlx` | `3_gold` | `victory_silver.event_attendances` + `victory_silver.event_registrations` + `victory_silver.events` + `victory_silver.equipping_enrollments` | `victory_gold.vw_person_event_history` | Scheduled (hourly, Dataform native) |
| `gold_equipping_completion.sqlx` | `3_gold` | `victory_silver.equipping_enrollments` + `victory_silver.persons` | `victory_gold.vw_equipping_completion` | Scheduled (hourly, Dataform native) |
| `gold_equipping_cohorts.sqlx` | `3_gold` | `victory_silver.equipping_classes` + `victory_silver.equipping_enrollments` | `victory_gold.vw_equipping_cohorts` | Scheduled (hourly, Dataform native) |
| `gold_leader_dashboard.sqlx` | `3_gold` | `victory_silver.victory_groups` + `victory_silver.victory_group_members` + `victory_silver.equipping_enrollments` + `victory_silver.event_attendances` + `victory_silver.ministry_memberships` | `victory_gold.vw_leader_dashboard` | Scheduled (hourly, Dataform native) |
| `gold_ministry_participation.sqlx` | `3_gold` | `victory_silver.ministry_memberships` + `victory_silver.ministry_catalog` | `victory_gold.vw_ministry_participation` | Scheduled (hourly, Dataform native) |
| `gold_pastoral_events.sqlx` | `3_gold` | `victory_silver.events` + `victory_silver.event_registrations` + `victory_silver.persons` | `victory_gold.vw_pastoral_events` | Scheduled (hourly, Dataform native) |
| `gold_admin_full.sqlx` | `3_gold` | `victory_silver.persons` + `victory_silver.person_occupations` + `victory_silver.person_contacts` + `victory_silver.equipping_enrollments` + `victory_silver.victory_groups` + `victory_silver.ministry_memberships` | `victory_gold.vw_admin_full` | Scheduled (hourly, Dataform native) |
| `gold_business_network.sqlx` | `3_gold` | `victory_silver.persons` + `victory_silver.person_occupations` | `victory_gold.vw_business_network` | Scheduled (hourly, Dataform native) |

> **Trigger note:** "Scheduled (hourly, Dataform native)" means the file runs as part of the full `workflow_config` cron run. "Pub/Sub (immediate, via Cloud Function)" means the file is also invoked as a scoped partial run when Cloud Function `dataform-attendance-trigger` fires — in addition to the hourly run.

### Resubmission Reconcile Logic (`stg_vg_members.sqlx` + `stg_victory_groups.sqlx`)

Both files implement **reconcile (replace)** behavior. The latest leader form submission is the authoritative source for active group membership.

**`stg_vg_members.sqlx`:**
- Members in the new Bronze submission but not currently active in Silver → INSERT new `victory_group_members` record.
- Members currently `is_active = TRUE` in Silver but absent from the new submission → UPDATE `is_active = FALSE`, `removed_at = submission_timestamp`.
- Members present in both → no change.

**`stg_victory_groups.sqlx`:**
- Groups in the new submission but not in Silver → INSERT (SCD2 new row).
- Groups currently `is_current = TRUE` for the same leader but absent from the new submission → SCD2 close (`valid_to = NOW()`, `is_current = FALSE`, `is_active = FALSE`).
- Groups present in both → SCD2 upsert of any changed fields if applicable.

This prevents stale active member and group records from accumulating when leaders update their rosters.

**Dataform assertions:** Each `.sqlx` file includes assertions that verify data quality before writing to the next layer (e.g. `assert person_id IS NOT NULL`, `assert email matches regex pattern`). A failing assertion stops the pipeline and sends an alert — bad data never reaches Gold.

**`stg_persons.sqlx` required assertions:**
- `assert_single_active_per_google_uid`: Detects two `is_current = TRUE` rows with the same non-NULL `google_uid` (Priority 0 duplicate signal — sets `duplicate_flag = TRUE` on both affected records and routes them to Tab 2).
- `assert_google_uid_uniqueness`: Halts the pipeline if the above condition is not resolved.

**Gold view mandatory assertion (applies to all Gold SQLX files that join `event_registrations`):**
```sql
assert_no_cancelled_event_registrations as (
  SELECT r.registration_id
  FROM ${ref("event_registrations")} r
  JOIN ${ref("events")} e ON r.event_id = e.event_id
  WHERE e.status = 'cancelled'
)
-- Non-empty result means a Gold view is exposing registrations for cancelled events.
-- Halts pipeline. All affected Gold views MUST filter WHERE events.status != 'cancelled'.
```
Affected Gold SQLX files that must include this assertion: `gold_events.sqlx`, `gold_engagement.sqlx`, `gold_event_history.sqlx`, `gold_funnel.sqlx`, `gold_equipping_completion.sqlx`, `gold_admin_full.sqlx`. See [REPORTING.md](REPORTING.md) for the binding filter rule.

### Gold View Dependency DAG

Gold views must be processed in dependency order during Dataform compilation. All Gold views in this system read exclusively from Silver tables — there are **zero Gold-on-Gold view dependencies**. Any future Gold-on-Gold chain MUST be reviewed by `@architect` and documented here before implementation.

**All Gold views — Tier 1 (direct Silver dependencies only):**

| Gold SQLX File | Silver Sources |
| :--- | :--- |
| `gold_demographics.sqlx` | `victory_silver.persons` |
| `gold_headcounts.sqlx` | `victory_silver.headcounts` + `victory_silver.events` |
| `gold_vg_summary.sqlx` | `victory_silver.victory_groups` + `victory_silver.victory_group_members` |
| `gold_ministry_participation.sqlx` | `victory_silver.ministry_memberships` + `victory_silver.ministry_catalog` |
| `gold_pastoral_events.sqlx` | `victory_silver.events` + `victory_silver.event_registrations` + `victory_silver.persons` |
| `gold_business_network.sqlx` | `victory_silver.persons` + `victory_silver.person_occupations` |
| `gold_equipping_completion.sqlx` | `victory_silver.equipping_enrollments` + `victory_silver.persons` |
| `gold_equipping_cohorts.sqlx` | `victory_silver.equipping_classes` + `victory_silver.equipping_enrollments` |
| `gold_events.sqlx` | `victory_silver.events` + `victory_silver.event_attendances` |
| `gold_engagement.sqlx` | `victory_silver.event_attendances` + `victory_silver.event_registrations` |
| `gold_event_history.sqlx` | `victory_silver.event_attendances` + `victory_silver.event_registrations` + `victory_silver.events` + `victory_silver.equipping_enrollments` |
| `gold_funnel.sqlx` | `victory_silver.equipping_enrollments` + `victory_silver.equipping_classes` + `victory_silver.persons` |
| `gold_leader_dashboard.sqlx` | `victory_silver.victory_groups` + `victory_silver.victory_group_members` + `victory_silver.equipping_enrollments` + `victory_silver.event_attendances` + `victory_silver.ministry_memberships` |
| `gold_admin_full.sqlx` | `victory_silver.persons` + `victory_silver.person_occupations` + `victory_silver.person_contacts` + `victory_silver.equipping_enrollments` + `victory_silver.victory_groups` + `victory_silver.ministry_memberships` |

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
    "event_id": "<victory_silver.events.event_id UUID>",
    "person_id": "<victory_silver.persons.person_id UUID>",
    "attendance_id": "<victory_silver.event_attendances.attendance_id UUID>"
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
- The Cloud Function invocation is **scoped to `stg_attendances.sqlx` and `discipleship_pipeline.sqlx` only** (not a full warehouse run). This minimizes BigQuery slot usage. Note: the `event_id` in the Pub/Sub payload is metadata for the Cloud Function — Dataform itself processes all pending Bronze records in those two files, not only the triggering event. There is no per-event-id filter inside Dataform.
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
victory_bronze.raw_form_submissions        victory_bronze.raw_event_actions         victory_bronze.raw_headcounts
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
victory_silver.persons (SCD2 · core)              victory_silver.person_occupations (SCD2)
─────────────────────────────             ──────────────────────────────────────
person_id · google_uid                    occupation_id · person_id
first_name · middle_name                  employment_type (employed|self_employed)
last_name · suffix · full_name            nature_of_work · company_name
email · address                   nature_of_business · business_name
is_in_victory_group                       valid_from · valid_to · is_current
vg_leader_first_name · vg_leader_last_name
journey_stage · review_status · source    victory_silver.equipping_classes
one2one_completed · one2one_date          ──────────────────────────────────────
duplicate_flag · duplicate_of_person_id   class_id · canonical_step
profile_completeness_pct                  class_name · batch_code
gender · birthdate · civil_status         facilitator_person_id
valid_from · valid_to · is_current        start_date · end_date · capacity
                                          status: upcoming|ongoing|completed|cancelled

victory_silver.victory_groups (SCD2)              victory_silver.equipping_enrollments
──────────────────────────────────────    ──────────────────────────────────────
group_id · leader_person_id               enrollment_id · class_id · person_id
group_name · group_type                   step_name_as_completed
(single|wives|husbands|students|young_pro)enrollment_status: enrolled|completed|dropped
is_active                                 enrolled_at · completed_at · dropped_at
valid_from · valid_to · is_current

victory_silver.victory_group_members              victory_silver.event_registrations                victory_silver.headcounts
──────────────────────────────────────    ──────────────────────────────────────    ──────────────────────────────────────
membership_id · group_id · person_id      registration_id · event_id · person_id    headcount_id · date · event_type
member_first_name · member_last_name      status: registered|attended|no_show|cancelled event_id · attendee_count
is_active · added_at · removed_at        payment_status · amount_paid · payment_ref submitted_by · submitted_at
                                          registered_at · registration_source
```

### Gold Views (read-only, row-secured)

| View Name | Audience |
| :--- | :--- |
| `victory_gold.vw_member_demographics` | Executive + Admin |
| `victory_gold.vw_equipping_funnel` | Executive + Admin |
| `victory_gold.vw_equipping_completion` | Admin |
| `victory_gold.vw_equipping_cohorts` | Admin |
| `victory_gold.vw_event_participation` | Executive + Admin |
| `victory_gold.vw_attendance_headcounts`| Executive + Admin |
| `victory_gold.vw_person_engagement` | Executive + Admin |
| `victory_gold.vw_person_event_history` | Admin + Leader (filtered) |
| `victory_gold.vw_victory_group_summary` | Executive + Admin |
| `victory_gold.vw_leader_dashboard` | VG Leader — `SESSION_USER()` row policy |
| `victory_gold.vw_ministry_participation` | Executive + Admin |
| `victory_gold.vw_pastoral_events` | Admin only |
| `victory_gold.vw_admin_full` | Admin only |
| `victory_gold.vw_business_network` | Admin only |


---

*Owner: @architect. Last updated: 2026-02-24. v4.6 amendments applied.*
