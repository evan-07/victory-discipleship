# Backend API — Cloud Run + FastAPI

← Part of [ARCHITECTURE.md](../ARCHITECTURE.md) | See also: [SCHEMA.md](SCHEMA.md) · [DATA_PIPELINE.md](DATA_PIPELINE.md) · [SECURITY.md](SECURITY.md)

---

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
| `POST /api/submit` | POST | `authenticated` | VG Leader form and Member Profile form submission — writes to bronze |
| `GET /api/me` | GET | authenticated | Returns current user's profile by `google_uid` |
| `GET /api/persons` | GET | admin | List persons. Supports `?q=<name>` for name search (used in VG member linking and intern search). Returns matching `victory_silver.persons` records (`is_current = TRUE`, `review_status IN ('pending', 'approved')` — rejected records excluded). Ordered by relevance. Minimum query length: 2 characters. Response: `[{ "person_id": "uuid", "full_name": "string", "journey_stage": "...", "review_status": "pending|approved" }]`. |
| `PATCH /api/persons/{id}` | PATCH | admin | Update a person record. Must implement SCD2 close-and-insert — see Write-Path Ownership Matrix. |
| `POST /api/persons/{id}/promote-to-leader` | POST | admin | Atomic promotion to VG Leader. Simultaneously (1) INSERTs `vg_leader` role into `victory_silver.person_roles` and (2) SCD2 PATCHes `journey_stage = 'leader'` on `victory_silver.persons`. Both operations succeed or both fail — no partial state. **Idempotent:** if an active `vg_leader` role already exists, the INSERT is skipped; if `journey_stage` is already `'leader'`, the SCD2 is skipped. Whichever field is out of sync is corrected atomically. Returns the updated person record and a flag `has_active_intern_relationship` so the frontend can surface the Step 5 inline prompt. Response: `{ "person": { ...person record... }, "has_active_intern_relationship": true/false, "active_intern_relationship_id": "uuid \| null" }`. |
| `GET /api/events` | GET | admin, executive | List all events |
| `POST /api/events` | POST | admin | Create new event instance |
| `GET /api/events/{slug}/pre-check` | GET | authenticated | Pre-registration check: person exists, profile completeness, duplicate registration check, upcoming event list |
| `POST /api/events/{slug}/self-register` | POST | authenticated | Self-register for a public event. Returns 409 if already registered. |
| `POST /api/events/{id}/register` | POST | admin | Admin registers a person for an event |
| `POST /api/events/{id}/attend` | POST | admin | Mark attendance post-event. Writes attendance to `victory_bronze.raw_event_actions` → Dataform creates `event_attendances`. Also updates `event_registrations.status = 'attended'` in-place for the matching registration record. Triggers discipleship pipeline for equipping step completion. |
| `POST /api/headcounts` | POST | admin | Submit anonymous headcount for an event or Sunday Service |
| `GET /api/leaders/me` | GET | `vg_leader` | Full leader profile — personal info, active Victory Groups (with member lists), and intern relationships. Used by `/leader.html` form pre-fill and `/dashboard.html`. Performs the same account-claiming fallback as `GET /api/me` when no `google_uid` match is found. |
| `PATCH /api/vg-members/{id}/link` | PATCH | admin | Link a VG member name record to an existing `person_id`. Body: `{ "person_id": "<uuid>" }`. Response 200: `{ "membership_id": "uuid", "group_id": "uuid", "person_id": "uuid", "member_first_name": "string", "member_last_name": "string", "is_active": true }`. |
| `GET /api/intern-relationships` | GET | admin | List intern relationship records. Supports `?status=pending` filter for admin review queue. Returns `intern_person_id`, `leader_person_id`, `review_status`, `is_active`, `source`, `start_date`. |
| `POST /api/intern-relationships` | POST | admin | Create an intern relationship directly (admin-initiated, bypasses leader form). `review_status` defaults to `approved` for admin-created records. `source = 'admin_created'`. |
| `PATCH /api/intern-relationships/{id}` | PATCH | admin | Approve, reject, or deactivate an intern relationship. Permitted field updates: `review_status` (`approved` / `rejected`), `is_active` (`FALSE` to close), `end_date`. Used for both admin review of leader-form submissions and closing relationships when an intern is promoted to VG Leader. |
| `PATCH /api/intern-relationships/{id}/link` | PATCH | admin | Link an unresolved intern relationship to an existing `victory_silver.persons` record. Body: `{ "intern_person_id": "<uuid>" }`. Required before an `intern_relationships` record with `intern_person_id = NULL` can be approved. |
| `GET /api/health` | GET | public | Health check endpoint (for Cloud Run uptime) |
| `POST /api/persons` | POST | admin | Create a new Contact-stage person record directly (admin "Create Profile" tool — accessible from `/admin.html`). Writes to `victory_silver.persons` with `source = 'admin_created'`, `review_status = 'approved'`, `google_uid = NULL`. This is a direct Silver write — no Bronze record is created. Request body: `{ "first_name": "string", "middle_name": "string \| null", "last_name": "string", "suffix": "string \| null", "address": "string", "birthdate": "YYYY-MM-DD", "email": "string \| null", "contact_number": "string", "facebook_profile": "string \| null" }`. Response 201: the created `victory_silver.persons` record with all fields including `person_id`, `source = 'admin_created'`, `review_status = 'approved'`, `google_uid = null`. |
| `PATCH /api/persons/{id}/contacts` | PATCH | admin | SCD2 close-and-insert update on a `person_contacts` record (e.g., update mobile or facebook contact value). |
| `PATCH /api/persons/{id}/occupations` | PATCH | admin | SCD2 close-and-insert update on a `person_occupations` record (e.g., correct employment type or company name). |
| `PATCH /api/events/{id}` | PATCH | admin | Update event status (`registration_open` / `closed` / `completed` / `cancelled`), `hero_image_url`, `capacity`, or `end_datetime`. |
| `PATCH /api/event-registrations/{id}` | PATCH | admin | Update payment status (`pending` → `paid` / `waived`), `payment_ref`, `payment_method`, `amount_paid`, and/or registration status (`no_show` / `attended`). |
| `PATCH /api/victory-groups/{id}` | PATCH | admin | Deactivate a Victory Group (`is_active = FALSE`). Also sets all active `victory_group_members` for that group to `is_active = FALSE`. SCD2 close on `victory_groups`. |
| `PATCH /api/vg-members/{id}` | PATCH | admin | Deactivate a VG member (sets `is_active = FALSE`, `removed_at = NOW()`). Distinct from `PATCH /api/vg-members/{id}/link`, which links a person_id only. |
| `POST /api/equipping-classes` | POST | admin | Create a new equipping class batch (fields: `canonical_step`, `class_name`, `batch_code`, `facilitator_person_id`, `start_date`, `end_date`, `capacity`). |
| `PATCH /api/equipping-classes/{id}` | PATCH | admin | Update class `status` (`upcoming` / `ongoing` / `completed` / `cancelled`), `end_date`, or `capacity`. |
| `POST /api/equipping-enrollments` | POST | admin | Enroll a person in an equipping class. Creates `equipping_enrollments` record with `enrollment_status = 'enrolled'`. |
| `PATCH /api/equipping-enrollments/{id}` | PATCH | admin | Correct enrollment status (`enrolled` → `dropped`; or manual override to `completed`). |
| `POST /api/ministry-catalog` | POST | admin | Create a new ministry entry in `ministry_catalog`. |
| `POST /api/ministry-memberships` | POST | admin | Add a person to a ministry. Creates `ministry_memberships` record with `status: interested` or `active`. |
| `PATCH /api/ministry-memberships/{id}` | PATCH | admin | Update membership status (`interested` → `active` → `inactive`). |
> **Intern auto-match algorithm:** When a VG Leader submits an intern name in Section 3 of the leader form, `stg_intern_relationships.sqlx` attempts an **exact, case-insensitive match** on `first_name + last_name` against `victory_silver.persons` (`is_current = TRUE`). Exactly one match → `intern_person_id` is populated automatically. Zero matches or multiple matches → `intern_person_id = NULL`; the record surfaces in **Tab 3 (Unresolved Interns)** of the admin queue for manual linking via `PATCH /api/intern-relationships/{id}/link`. Admin uses `GET /api/persons?q=<name>` to search for the correct person record.

### Authentication Flow

Copy
```plaintext
1. User opens app → Firebase Auth SDK prompts Google Sign-In if not authenticated
2. Firebase returns a signed JWT ID token (valid 1 hour, auto-refreshed)
3. Frontend includes JWT as Authorization: Bearer <token> on every API call
4. Cloud Run FastAPI middleware calls Firebase Admin SDK to verify JWT signature
5. If valid: extract email → look up role in victory_silver.person_roles → attach to request context
6. Route-level decorators check required role → allow or return 403 Forbidden
```
### `GET /api/me` — Response Schema

Returns a unified profile object assembled by Cloud Run from multiple Silver tables (all `is_current = TRUE`).

**HTTP 200 — Person found:**
```json
{
  "person_id": "uuid",
  "google_uid": "string",
  "first_name": "string",
  "middle_name": "string | null",
  "last_name": "string",
  "suffix": "string | null",
  "full_name": "string",
  "address": "string | null",
  "birthdate": "YYYY-MM-DD | null",
  "email": "string | null",
  "journey_stage": "contact|member|intern|leader",
  "review_status": "pending|approved|rejected",
  "one2one_completed": false,
  "one2one_date": "YYYY-MM-DD | null",
  "is_in_victory_group": "boolean | null",
  "vg_leader_first_name": "string | null",
  "vg_leader_last_name": "string | null",
  "contacts": [
    { "contact_type": "mobile|facebook|email|...", "contact_value": "string" }
  ],
  "occupations": [
    { "employment_type": "employed|self_employed", "nature_of_work": "string | null",
      "company_name": "string | null", "nature_of_business": "string | null",
      "business_name": "string | null" }
  ],
}
```

- `contacts` contains all `is_current = TRUE` `person_contacts` records for this person.
- `occupations` contains the current `is_current = TRUE` `person_occupations` record(s).
- Victory Groups and intern relationships are **not** returned by this endpoint. Use `GET /api/leaders/me` for leader-specific data.

**HTTP 404 — Person not found by google_uid:**
Cloud Run first attempts to match `google_uid`. If no match, it attempts **account-claiming** (see below). If claiming also fails, returns `{ "detail": "Person not found." }`. Frontend shows: *"Your profile was not found. Please ask your Victory Group leader or admin to create your profile."*

### Account-Claiming Flow (Admin-Created Records on First Sign-In)

When `GET /api/me` finds no match by `google_uid`, Cloud Run attempts an email-based fallback:

```plaintext
1. Person signs in with Google on any page.
2. Frontend calls GET /api/me with JWT.
3. Cloud Run: SELECT * FROM victory_silver.persons
   WHERE google_uid = <jwt.uid> AND is_current = TRUE → no match.
4. Cloud Run fallback: SELECT * FROM victory_silver.persons
   WHERE email = <jwt.email> AND google_uid IS NULL AND is_current = TRUE.
5. One match → Cloud Run directly UPDATEs persons.google_uid = <jwt.uid>
   (direct UPDATE, NOT SCD2 — updating the auth link is not a business data change).
   Logs to data_change_log. Returns the claimed person record as the GET /api/me response.
6. Zero matches → returns HTTP 404.
   Frontend shows: "Your profile was not found. Please contact admin."
7. Multiple matches → Cloud Run returns the oldest record (lowest valid_from) and logs
   a data inconsistency flag to data_change_log for admin review.
8. Claiming is transparent — no confirmation screen is shown to the user.
```

> **Write-Path Matrix exception:** The `persons.google_uid` direct UPDATE is the second permitted Cloud Run direct Silver write (alongside the two-phase write for new-user event registration). It updates only the `google_uid` field on an existing row — no SCD2 close-and-insert required, as this is an auth linking operation, not a business data change.

### `GET /api/leaders/me` — Response Schema

Returns the full leader profile assembled from multiple Silver tables. Only accessible to users with the `vg_leader` role. Performs the same account-claiming fallback as `GET /api/me` when no `google_uid` match is found.

**HTTP 200 — Leader found:**
```json
{
  "person_id": "uuid",
  "google_uid": "string",
  "first_name": "string",
  "middle_name": "string | null",
  "last_name": "string",
  "suffix": "string | null",
  "full_name": "string",
  "address": "string | null",
  "birthdate": "YYYY-MM-DD | null",
  "email": "string | null",
  "journey_stage": "leader",
  "review_status": "pending|approved|rejected",
  "one2one_completed": true,
  "one2one_date": "YYYY-MM-DD | null",
  "vg_leader_first_name": "string | null",
  "vg_leader_last_name": "string | null",
  "contacts": [
    { "contact_type": "mobile|facebook|email|...", "contact_value": "string" }
  ],
  "occupations": [
    { "employment_type": "employed|self_employed", "nature_of_work": "string | null",
      "company_name": "string | null", "nature_of_business": "string | null",
      "business_name": "string | null" }
  ],
  "victory_groups": [
    { "group_id": "uuid", "group_type": "single|wives|husbands|students|young_pro", "group_name": "string | null",
      "is_active": true,
      "members": [
        { "membership_id": "uuid", "member_first_name": "string", "member_last_name": "string",
          "person_id": "uuid | null", "is_active": true }
      ]
    }
  ],
  "intern_relationships": [
    { "relationship_id": "uuid", "intern_first_name": "string", "intern_last_name": "string",
      "intern_person_id": "uuid | null", "review_status": "pending|approved", "is_active": true }
  ]
}
```

- `victory_groups` contains all `is_active = TRUE`, `is_current = TRUE` groups where `leader_person_id` matches this person, including their nested `members`.
- `intern_relationships` contains all `is_active = TRUE` relationships where `leader_person_id` matches this person.
- Used by `/leader.html` (form pre-fill) and `/dashboard.html` (leader dashboard).

**HTTP 404 — Leader not found:** Same account-claiming fallback logic as `GET /api/me`. Returns `{ "detail": "Person not found." }` if both `google_uid` and email-match fail.

### `POST /api/submit` — Request Schema

Used by `/leader.html` (VG Leader form) and `/profile.html` (Member Profile form). Writes the full payload to `victory_bronze.raw_form_submissions`.

```json
{
  "source_page": "leader | profile",
  "personal": {
    "first_name": "string",
    "middle_name": "string | null",
    "last_name": "string",
    "suffix": "string | null",
    "address": "string",
    "contact_number": "string",
    "birthdate": "YYYY-MM-DD",
    "facebook_profile": "string | null"
  },
  "employment": {
    "employment_type": "employed | self_employed",
    "nature_of_work": "string | null",
    "company_name": "string | null",
    "nature_of_business": "string | null",
    "business_name": "string | null"
  },
  "vg_leader": {
    "first_name": "string | null",
    "last_name": "string | null"
  },
  "groups": [
    {
      "group_type": "single | wives | husbands | students | young_pro",
      "group_name": "string | null",
      "members": [
        { "first_name": "string", "last_name": "string" }
      ]
    }
  ],
  "interns": [
    { "first_name": "string", "last_name": "string" }
  ]
}
```

- `groups` and `interns` are present only when `source_page = 'leader'`. Both are empty arrays `[]` in the Member Profile form submission.
- `employment` is optional for Contact-stage event registrations (submitted via `POST /api/events/{slug}/self-register`).
- Backend validation (Pydantic): required fields validated before writing to Bronze. Returns HTTP 422 on validation failure.

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

> **Note:** The following example is for a **Member-stage person** — `facebook_profile` appears in `missing_fields` because it is required from Member stage onward. For a Contact-stage person, `facebook_profile` would not appear in `missing_fields` (encouraged but non-blocking at that stage).

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
2. Query `victory_silver.events` for the given `slug`. If not found → return 404. If `status != 'registration_open'` → return 410 Gone with `{ "event_status": "<status>", "message": "Registration is not open for this event." }`. Frontend shows an appropriate closed/cancelled screen — no registration is possible.
3. Query `victory_silver.persons` for matching `google_uid` (WHERE `is_current = TRUE`). If no match, attempt an email-based account-claiming fallback: query `victory_silver.persons WHERE email = <jwt.email> AND google_uid IS NULL AND is_current = TRUE`. If exactly one match is found, claim the account (direct UPDATE `google_uid = <jwt.uid>`, log to `data_change_log`) and continue as `person_found: true` with the claimed record. If zero or multiple matches, continue as `person_found: false`. **Developer note:** Extract the account-claiming logic as a shared function reused by both `GET /api/me` and this endpoint — assess implementation complexity before committing.
4. If person found → query `victory_silver.event_registrations` for this event + person (WHERE `status != 'cancelled'`).
5. If person found → query `victory_silver.event_registrations` for ALL upcoming events (WHERE `event.start_datetime > NOW()` AND `status IN ('registered')`).
6. Compute `profile_complete` by checking Contact-stage required fields: `first_name`, `middle_name`, `last_name`, `address`, `birthdate` on `victory_silver.persons`, and `contact_number` via LEFT JOIN on `victory_silver.person_contacts WHERE contact_type = 'mobile' AND is_current = TRUE`. `suffix` is excluded — the form always pre-populates it with 'None' and it is never NULL after submission. `facebook_profile` is checked via LEFT JOIN on `victory_silver.person_contacts WHERE contact_type = 'facebook' AND is_current = TRUE` — **only included in `missing_fields` and counted against `profile_complete` when `persons.journey_stage IN ('member', 'intern', 'leader')`**. For `journey_stage = 'contact'`, Facebook is encouraged but non-blocking and must not appear in `missing_fields`. If any required field is NULL or missing, `profile_complete = false` and `missing_fields` is populated.
7. Return assembled response.

> **Known limitation:** For a new user created via the two-phase write (Scenario 1), `profile_completeness_pct` on `victory_silver.persons` defaults to `0` until the next Dataform run (up to 1 hour). If the same user visits a second event landing page within this window, the backend computes completeness dynamically via the JOINs above (step 6) rather than relying on `profile_completeness_pct` — ensuring the pre-check returns an accurate result. `profile_completeness_pct` is used for reporting and admin views only. It is not used by the pre-check endpoint.

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
        "SELECT * FROM victory_silver.event_registrations "
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

**Optional profile payload (Scenarios 1 and 4):**

For new users (Scenario 1 — `person_found: false`) and returning users with incomplete profiles (Scenario 4 — `profile_complete: false`), the request body may include an optional `profile` object:

```json
{
  "profile": {
    "first_name": "string",
    "middle_name": "string",
    "last_name": "string",
    "suffix": "string | null",
    "address": "string",
    "contact_number": "string",
    "birthdate": "YYYY-MM-DD",
    "facebook_profile": "string | null",
    "is_in_victory_group": "boolean | null"
  }
}
```

**Backend logic when `profile` is present:**
1. Write the full profile to `victory_bronze.raw_form_submissions` with `source_page = 'event_registration'`.
2. **Scenario 1 (new user):** Create a minimal Silver `persons` record immediately — `person_id` (new UUID), `google_uid`, `first_name`, `last_name`, `review_status = 'pending'`, `source = 'event_registration'`, `journey_stage = 'contact'`, `is_current = TRUE`, `valid_from = NOW()`. This is the two-phase write exception. Then create `event_registrations` using the new `person_id`. Return `201` with success.
3. **Scenario 4 (incomplete profile):** The `person_id` is already known from the pre-check response. Create `event_registrations` immediately using the existing `person_id`. Dataform reconciles the profile updates (missing fields) on the next scheduled run. Return `201` with success.
4. If `profile` is absent but `person_found: false` → return `422` (profile required for new users).

### Discipleship Auto-Pipeline (Event Attendance → Enrollment Completion)

Events and equipping classes are separate systems. Equipping enrollment is exclusively admin-managed via class rosters. The discipleship pipeline does **not** create new enrollment records — it marks existing `enrolled` records as `completed` when admin confirms attendance at an equipping event session.

**Pre-condition:** Admin must enroll a person in an equipping class (via the admin class roster, setting `enrollment_status = 'enrolled'`) before marking attendance. The pipeline finds that enrollment record and updates it — if no enrolled record exists, the pipeline is a no-op for that person.

Copy
```plaintext
1. Admin pre-enrolls persons in a class via the admin class roster portal.
   victory_silver.equipping_enrollments created with enrollment_status = 'enrolled'.

2. Admin POSTs to /api/events/{id}/attend with person_id (at the actual class session).

3. Cloud Run writes attendance to victory_bronze.raw_event_actions (immediate, streaming insert).

4. Cloud Run publishes a Pub/Sub message. Cloud Function dataform-attendance-trigger fires.

5. Dataform stg_attendances.sqlx reads from bronze → MERGE-upserts to victory_silver.event_attendances.

6. Dataform discipleship_pipeline.sqlx reads from:
     victory_silver.event_attendances + victory_silver.event_type_catalog
     + victory_silver.equipping_enrollments + victory_silver.equipping_classes
   → UPDATES victory_silver.equipping_enrollments SET
       enrollment_status = 'completed',
       completed_at = checked_in_at
   WHERE person has an 'enrolled' record whose equipping_classes.canonical_step
     matches the event's event_type_catalog.equipping_step.
   Short-circuits (no-op) when equipping_step IS NULL on the event.
   If multiple enrolled records exist for the same step, the most recent (by enrolled_at) is updated.

7. Gold views update automatically — Looker Studio reflects the change on next data refresh.
```

> **Write-path rule:** Cloud Run writes attendance data to `bronze` only. `victory_silver.event_attendances` is owned exclusively by Dataform. `victory_silver.equipping_enrollments` is created by admin via the admin portal (enrolled status) and updated to `completed` by the Dataform pipeline after attendance is confirmed. Admin corrections to existing silver records are permitted directly via admin portal PATCH endpoints, but initial attendance records always originate from bronze via the Dataform pipeline.
>
> **Enrollment rule:** The pipeline never auto-creates enrollment records. Admin must enroll a person before attendance can trigger a completion update. This preserves the pastoral oversight principle — a person cannot be marked as completing an equipping step without deliberate admin enrollment.

### Write-Path Ownership Matrix

This table is the authoritative reference for which component is permitted to write to each Silver table and what write pattern it must follow. Deviating from this table requires an `@architect` review and a Decision Log entry.

| Silver Table | Dataform (scheduled) | Cloud Run (API) | Write Pattern |
| :--- | :--- | :--- | :--- |
| `persons` | ✅ Owns initial creation + SCD2 upsert | ✅ Exception 1: minimal record on new-user event registration (two-phase write). Exception 2: direct UPDATE of `google_uid` field only on account-claiming (first sign-in email match — not SCD2). Admin PATCH: SCD2 close-and-insert. `POST /api/persons` (admin create): direct INSERT. | SCD2 for business data changes. Direct UPDATE/INSERT for auth linking and admin creation only. |
| `person_contacts` | ✅ Owns initial creation + SCD2 upsert | ✅ Admin PATCH: SCD2 close-and-insert. | SCD2 |
| `person_occupations` | ✅ Owns initial creation + SCD2 upsert | ✅ Admin PATCH: SCD2 close-and-insert. | SCD2 |
| `victory_groups` | ✅ Owns initial creation + SCD2 upsert | ✅ Admin PATCH: SCD2 close-and-insert. | SCD2 |
| `victory_group_members` | ✅ Owns initial creation | ✅ Admin PATCH (link/unlink): direct UPDATE (not SCD2 — no history tracking on `person_id` link). | Direct UPDATE on `person_id` field only. |
| `person_roles` | ❌ Not managed by Dataform | ✅ Admin only: INSERT new role record. Deactivation: `is_active = FALSE` UPDATE. | INSERT for new roles; direct UPDATE for deactivation. |
| `intern_relationships` | ✅ INSERTs new `pending` records from Bronze form data | ✅ Admin only: PATCH to set `review_status = 'approved' / 'rejected'`, `is_active = FALSE`, `end_date`. | Dataform INSERTs; admin PATCHes status fields in-place (not SCD2). |
| `equipping_classes` | ❌ Not managed by Dataform | ✅ Admin only: full CRUD. | Direct INSERT/UPDATE. |
| `equipping_enrollments` | ✅ UPDATEs `enrolled → completed` via discipleship pipeline | ✅ Admin: INSERT (`enrolled` status), PATCH (status corrections). | Dataform UPDATE; admin INSERT/PATCH. |
| `events` | ✅ Creates from Bronze `action_type = 'created'` | ✅ Admin PATCH (status, capacity, hero image). | Dataform INSERT; admin PATCH in-place. |
| `event_registrations` | ❌ Not managed by Dataform | ✅ Cloud Run direct INSERT via self-register endpoint (all public scenarios), admin-register endpoint, and new-user two-phase write exception. Admin PATCH (status, payment fields). `POST /api/events/{id}/attend` also updates `status = 'attended'` in-place. | Cloud Run INSERT; admin PATCH in-place. Note: `raw_event_actions action_type = 'registered'` is not used — no flow writes this action type to Bronze. |
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



---

*Owner: @architect. Last updated: 2026-02-24. v4.6 amendments applied.*
