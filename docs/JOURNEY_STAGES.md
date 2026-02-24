# Person Lifecycle, Journey Stages & Equipping Pathway

← Part of [ARCHITECTURE.md](../ARCHITECTURE.md) | See also: [EVENTS.md](EVENTS.md) · [SCHEMA.md](SCHEMA.md) · [UX_FLOWS.md](UX_FLOWS.md)

---

## Person Lifecycle & Journey Stages

`journey_stage` is a single admin-managed field on `victory_silver.persons`. It is never auto-computed or inferred from other fields. This preserves pastoral judgment — only a leader who knows the person can accurately assess their stage.

### The Four Stages

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
| First Name | victory_silver.persons.first_name | |
| Middle Name | victory_silver.persons.middle_name | Common in PH (mother's maiden name) |
| Last Name | victory_silver.persons.last_name | |
| Suffix | victory_silver.persons.suffix | Jr., Sr., III, etc. — None if not applicable |
| Address | victory_silver.persons.address | Full address, single text field |
| Contact Number | victory_silver.person_contacts (type: mobile) | |
| Birthday | victory_silver.persons.birthdate | |
| Facebook Profile | victory_silver.person_contacts (type: facebook) | URL or profile name — **encouraged at Contact stage, required from Member stage onward** |

### Stage 02 — Member

- **Definition:** Completed One2One, part of the movement. Consumer stage.
- **Entry point:** Admin records `one2one_completed = true` and `one2one_date`. Sets `journey_stage = member`.
- **Characteristics:** Part of a Victory Group as a member. Attends events and services.
- **Self-service data collection:** VG Members submit their employment info and VG Leader name via `/profile.html` (Google Sign-In). The form pre-fills from their existing Silver record and writes to `victory_bronze.raw_form_submissions`. Dataform reconciles on the next scheduled run. Admin may also enter this data directly via the admin portal.
- **Admin portal soft-warning:** When admin sets `journey_stage = member`, the portal checks whether `vg_leader_first_name` and `vg_leader_last_name` are populated. If either is missing, a soft warning is displayed: *"VG Leader name is missing for this member. Please collect and enter it."* This does **not** block the stage transition — admin may proceed — but the warning ensures the gap is visible. The record will appear with a low `profile_completeness_pct` in admin views until resolved.
- **Next step:** Become a VG Intern while progressing through the Equipping Pathway.
- **Note on One2One:** The One2One completion is currently communicated verbally by the leader to admin. There is no system-triggered notification. Admin records it manually via PATCH on the person record.

**Required fields (all Contact fields plus):**

| Field | Storage Location | Notes |
| :--- | :--- | :--- |
| Employment Type | victory_silver.person_occupations.employment_type | employed or self_employed |
| If employed: Nature of Work | victory_silver.person_occupations.nature_of_work | e.g. Accounting, Engineering, Teaching |
| If employed: Company Name | victory_silver.person_occupations.company_name | |
| If self-employed: Nature of Business / Freelance Industry | victory_silver.person_occupations.nature_of_business | e.g. Food, Retail, Graphic Design |
| If self-employed: Business Name | victory_silver.person_occupations.business_name | |
| VG Leader First Name | victory_silver.persons.vg_leader_first_name | Name of their Victory Group leader |
| VG Leader Last Name | victory_silver.persons.vg_leader_last_name | |

### Stage 03 — VG Intern

- **Definition:** Being discipled, training to lead.
- **Entry point — two steps, both required:**
  1. **Admin** sets `journey_stage = intern` on the person's record in the admin portal.
  2. **VG Leader** identifies the intern on the VG Leader form (Section 3 — Interns I'm Supervising). This creates a `pending` `intern_relationships` record. Admin reviews and confirms in the admin portal, which activates the relational link (`review_status = 'approved'`, `is_active = TRUE`).
- **Sequencing:** Either step may happen first, but the `intern_relationships` record is not considered active until admin confirms it. The Silver pipeline only syncs `vg_leader_first_name/last_name` from an `approved` relationship.
- **Characteristics:** Active intern under a VG Leader. Listed in `victory_silver.intern_relationships` linked to their supervising leader (after admin confirmation).
- **Admin queue alert — unlinked interns:** The admin portal surfaces a dedicated alert queue for persons where `journey_stage = 'intern'` but no `intern_relationships` record with `review_status = 'approved'` and `is_active = TRUE` exists. These are interns who have been stage-promoted but whose relational link is pending, unresolved, or missing. Admin is prompted to either approve a pending relationship or create one directly via `POST /api/intern-relationships`.
- **Next step:** Lead their own group → becomes a VG Leader.

**Required fields:** Same as Member. The intern is still under a VG Leader and has the same data requirements.

**Leader linkage — two layers:**
- `vg_leader_first_name` / `vg_leader_last_name` on `victory_silver.persons` — display cache. Pre-populated when the person was at member stage and may reference a leader not yet in the system. Present at all stages.
- `victory_silver.intern_relationships.leader_person_id` — canonical FK for the intern-leader data relationship. Requires the supervising leader to be a registered `victory_silver.persons` record. `review_status = 'approved'` indicates the admin has confirmed the relationship. This is the authoritative relational link for interns.
- The Silver pipeline (`stg_persons.sqlx`) derives and keeps `vg_leader_first_name/last_name` in sync from the linked leader's `first_name`/`last_name` when a valid `leader_person_id` exists in `intern_relationships` with `review_status = 'approved'` and `intern_person_id IS NOT NULL`.
- If multiple active approved relationships exist for the same intern (edge case), the pipeline uses the most recent `start_date`.

### Stage 04 — VG Leader

- **Definition:** Leading their own Victory Group(s).
- **Entry point — five sequential admin actions (all required):**
  1. Person submits VG Leader form (`/leader.html`). Admin must wait until after the next Dataform run (up to 1 hour) for the leader's victory groups to appear in `victory_silver.victory_groups` before proceeding to Step 2.
  2. Admin reviews the submission in the admin portal (approves the person record — `review_status = 'approved'`).
  3. **Admin executes Steps 3 and 4 as a single atomic UI action:** The admin portal exposes a single **"Promote to VG Leader"** button on the person's record view. This button simultaneously (a) INSERTs the `vg_leader` role into `victory_silver.person_roles` and (b) SCD2 PATCHes `journey_stage = 'leader'` on `victory_silver.persons` in a single API call (`POST /api/persons/{id}/promote-to-leader`). The two operations are never performed as separate actions — splitting them creates a data inconsistency state. A person with mismatched role and stage is surfaced as a **data inconsistency warning** in the person's record view with a prompt to resolve.
  4. *(Included in Step 3 atomic action — see above.)*
  5. **Admin closes the person's active intern relationship** (if they were previously a VG Intern). Immediately after the "Promote to VG Leader" action completes, the admin portal checks for any active `intern_relationships` records (`is_active = TRUE`) for this person. If found, an **inline prompt** is displayed: *"This person has an active intern relationship with [Leader Name]. Close it now?"* with a **[ Close Relationship ]** button that calls `PATCH /api/intern-relationships/{id}` with `is_active = FALSE` and `end_date = today`. Admin must explicitly act — the system does not auto-close. If dismissed, the portal re-surfaces the open relationship as a warning on the person's record view until resolved.
- **Characteristics:** Has at least one active group in `victory_silver.victory_groups`. Fills in the VG Leader form. Has the `vg_leader` role in `victory_silver.person_roles`.
- **Encouraged to:** Complete Equipping Pathway if not already done. Go back for Spiritual Foundations if on old pathway.

**Required fields (all Member/Intern fields plus):**

| Field | Storage Location | Notes |
| :--- | :--- | :--- |
| Groups Led (count) | | Derived from victory_silver.victory_groups: COUNT of active groups where leader_person_id = this person |
| Type of Each Group | victory_silver.victory_groups.group_type | single · wives · husbands · students · young_pro |
| Members of Each Group | victory_silver.victory_group_members | First name + last name per member per group |

Note: The VG Leader form captures group and member information directly. The number of groups led is not a stored field — it is derived from the count of active victory_silver.victory_groups records for that leader.

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

### Core Fields on `victory_silver.persons`

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

---

## Equipping Pathway

Admin-managed, not self-reported. VG Leaders and Members are never asked what they've completed — the admin records it. The pathway has two valid versions (old and new). Both are permanently valid.

### New Pathway (2025–present)

| Step | Name | Canonical Key | Tracking Method |
| :--- | :--- | :--- | :--- |
| 1 | One2One | `one2one` | Fields on `victory_silver.persons` — not a class record |
| 2 | Spiritual Foundations | `spiritual_foundations` | `victory_silver.equipping_classes` + roster |
| 3 | Leadership 113 | `leadership_113` | `victory_silver.equipping_classes` + roster |

### Old Pathway (pre-2025, still valid)

| Step | Name | Canonical Key | Tracking Method |
| :--- | :--- | :--- | :--- |
| 1 | One2One | `one2one` | Fields on `victory_silver.persons` — not a class record |
| 2 | Victory Weekend | `victory_weekend` | `victory_silver.equipping_classes` + roster |
| 3 | Discipleship Class (aka Leader's Lab) | `discipleship_class` | `victory_silver.equipping_classes` + roster. `step_name_as_completed` preserves original name. |
| 4 | Leadership 113 | `leadership_113` | `victory_silver.equipping_classes` + roster |

Note on Leader's Lab: Leader's Lab was a temporary rename of Discipleship Class. Any record where step_name_as_completed = "Leader's Lab" maps to canonical_step = discipleship_class. This is handled in the Silver pipeline — historically accurate, reports correctly.

### Canonical Step Name Mapping

| Canonical Step | Historical Names | Pathway | How Tracked |
| :--- | :--- | :--- | :--- |
| `one2one` | One2One | Both | Fields on `victory_silver.persons` — not a class record |
| `victory_weekend` | Victory Weekend | Old only | `victory_silver.equipping_classes` + roster |
| `discipleship_class` | Discipleship Class, Leader's Lab | Old only | `victory_silver.equipping_classes` + roster — `step_name_as_completed` preserves original names |
| `spiritual_foundations` | Spiritual Foundations | New (encouraged for old) | `victory_silver.equipping_classes` + roster |
| `leadership_113` | Leadership 113 | Both | `victory_silver.equipping_classes` + roster |

### Pathway Completion Rules (Gold View Logic)

Completion logic lives in Gold views, not the Silver schema. When the pathway changes again, only `victory_gold.vw_equipping_completion` needs updating — no Silver schema changes, no data migration, no historical records touched.

| Completion Type | Definition | Action Surfaced |
| :--- | :--- | :--- |
| New pathway complete | Has `one2one` + `spiritual_foundations` + `leadership_113` | Fully equipped badge on person profile |
| Old pathway complete | Has `one2one` + `discipleship_class` + `leadership_113` | Fully equipped badge on person profile. Encouraged: add SF. |
| Old pathway complete but missing SF | Flag in admin view: "Encourage Spiritual Foundations" | |
| Ready for next step | Has Step N completed but not Step N+1 for their pathway | Listed in "Pathway Pipeline" drill-down per step |
| Victory Weekend legacy | Has `victory_weekend` | Shown in old pathway funnel, not new pathway funnel |

---

*Owner: @architect. Last updated: 2026-02-24.*
