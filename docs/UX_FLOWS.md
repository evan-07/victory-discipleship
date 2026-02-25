# Frontend & UX Flows

← Part of [ARCHITECTURE.md](../ARCHITECTURE.md) | See also: [API.md](API.md) · [JOURNEY_STAGES.md](JOURNEY_STAGES.md) · [EVENTS.md](EVENTS.md)

---

## Delivery Phases

This is the authoritative delivery reference. Use this table to track whether each audience is being served by the current build.

| Phase | Audience | Pages | Scope |
| :--- | :--- | :--- | :--- |
| **Phase 1 — MVP** | Anyone, VG Members, Admin team | `/e/[slug]` · `/profile` · `/admin` · `/events` | Event self-registration, member profile self-service, core admin portal (review queue, event management, person editing) |
| **Phase 2** | VG Leaders, Admin team | `/leader` · `/dashboard` | VG Leader self-reporting form, leader group dashboard, group & member lifecycle, intern relationship management, equipping class roster |
| **Phase 3** | Families / Couples, Admin team | `/e/[slug]` (pastoral form) | Pastoral event self-registration (Weddings, Child Dedications, Business Dedications). Admin-initiated pastoral remains available from Phase 1. |
| **Phase 4** | Executives | `/reports` | Embedded Looker Studio dashboards |

---

## Pages & Access Control

### Page Structure

| Page | Who Sees It | Access Control | Phase | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `/e/[slug]` | Anyone | Google Sign-In | **Phase 1** | Public event landing page — no nav. Smart pre-check drives registration flow. |
| `/profile.html` | VG Members | Google Sign-In | **Phase 1** | Own record view and edit. Pre-fills from Silver. Collects employment info and VG Leader name. Cannot see other records. |
| `/admin.html` | Admin only | Firebase Auth + role check (admin) | **Phase 1** | Core admin portal: review queue, person editing, role assignment. |
| `/events.html` | Admin only | Firebase Auth + role check (admin) | **Phase 1** | Event management: create event, manage status, view registrations, mark attendance. |
| `/leader.html` | VG Leaders | Google Sign-In | **Phase 2** | VG Leader self-reporting form — captures personal info, Victory Groups led, and interns supervised. Pre-fills for returning users. |
| `/dashboard.html` | VG Leaders | Firebase Auth + role check (`vg_leader`) | **Phase 2** | Personal group and discipleship overview for VG Leaders. |
| `/reports.html` | Executives | Firebase Auth + executive role; Looker Studio iframe embed | **Phase 4** | Embedded Looker Studio dashboards. No data editing. Direct Looker Studio links are not the delivery mechanism. |

### Mobile Responsiveness Strategy

- Bootstrap 5 grid provides mobile-first responsiveness for the existing member form.
- Build with Bootstrap breakpoints: `xs` (320px+), `sm` (576px+), `md` (768px+), `lg` (992px+).
- Test on real devices using Google AntiGravity's preview capabilities or BrowserStack free tier.
- Touch targets: minimum 44×44px for all interactive elements per WCAG 2.1.
- Font sizes: minimum 16px body text to prevent iOS auto-zoom on form fields.
- Viewport meta tag enforced: `width=device-width, initial-scale=1.0`.

---

## Phase 1 Flows
→ All Phase 1 UX flows are documented in [UX_FLOWS_PHASE1.md](UX_FLOWS_PHASE1.md).

---

## UX Flows
### Entry Points Summary

| Entry Point | URL | Who | Auth | Key Behavior | Phase |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Event Landing Page | `/e/[slug]` | Anyone | Google Sign-In | Smart pre-check → profile form or confirm or already-registered screen. VG question for new users. | **Phase 1** |
| Member Profile | `/profile.html` | VG Members | Google Sign-In | View and update own record. Pre-fills from Silver. Collects employment info and VG Leader name (member-stage required fields). Cannot see other records. | **Phase 1** |
| Admin Portal | `/admin.html` | Admin team | Google Sign-In + admin role | Review queue, event management, person editing, role assignment. | **Phase 1** |
| VG Leader Form | `/leader.html` | VG Leaders | Google Sign-In | New → blank form. Returning → full pre-fill. Captures personal info + groups + members. | **Phase 2** |
| Pastoral Event Page | `/e/[slug]` | Families / couples | Google Sign-In | Simplified public self-registration for pastoral events (Weddings, Dedications). Admin-initiated in Phase 1. | **Phase 3** |
| Reports | `/reports.html` | Executives | Google Sign-In + executive role | Embedded Looker Studio dashboards. No data editing. Direct Looker Studio links are not the delivery mechanism. | **Phase 4** |

> Phase 1 entry point flows (event registration scenarios, member profile form, admin portal) are in [UX_FLOWS_PHASE1.md](UX_FLOWS_PHASE1.md).

### VG Leader Form — New User Flow

> **Phase 2.** A "new user" in this context is a VG Leader who has been promoted by admin (`journey_stage = 'leader'`, `vg_leader` role active) and is accessing `/leader.html` **for the first time**. Their personal data already exists in Silver from their Member stage. Sections 2 and 3 are empty on first access — no Victory Groups or Interns have been submitted yet.

```plaintext
1. Leader opens /leader.html → Google Sign-In (one-tap if already signed in)
2. Frontend calls GET /api/leaders/me with JWT
3. Cloud Run looks up record by google_uid → returns full personal profile
   with groups: [] and interns: []
4. Frontend detects groups: [] → renders NEW USER state:
   Section 1 — Personal Info: ALL fields pre-filled from Silver record (all editable)
   Section 2 — Victory Groups Led: empty — shows "Add your first Victory Group" prompt
                                   with one blank group card already open
   Section 3 — Interns I'm Supervising: empty (optional — may be skipped on first submit)
5. Leader reviews/corrects Section 1, adds at least one group in Section 2,
   optionally adds interns in Section 3 → submits
6. POST /api/submit → writes to victory_bronze.raw_form_submissions
   with source_page = 'leader'
7. Success message: "Thank you, your data has been received."
8. On next load (after Dataform run — up to 1 hour): form transitions to
   Returning User state — groups and members appear pre-filled.
   Pre-Dataform banner shown in admin portal during this window (see below).
```

**Section 1 — first submission behavior:** All personal fields (name, address, contact number, birthday, gender, civil status, Facebook, employment info, VG Leader name) are pre-filled from the existing Silver record. All fields are editable. Any corrections write to Bronze and are SCD2-reconciled by Dataform on the next run.

**Section 2 — first submission behavior:** At least one Victory Group is required to submit. The form opens with one blank group card pre-rendered (type dropdown + empty member list). Leader must select group type and add at least one member name. Additional groups added via `[ + Add Another Group ]`.

**Section 3 — first submission behavior:** Entirely optional on first submission. Leader may skip if they are not currently supervising any interns.

**Edge case — person has no Silver record:** If `GET /api/leaders/me` finds no person record by `google_uid` and email-match also fails, the form renders the full blank new-person form (same Contact-stage fields as event registration Scenario 1: name, address, contact number, birthday, gender, civil status, Facebook, employment fields, VG question) prepended to Sections 2 and 3. Submission creates a new Contact-stage person in Silver via the standard write path. **This person will NOT have a `vg_leader` role — admin must promote them separately.**

---

### VG Leader Form — Returning User Flow

> **Phase 2.** The VG Leader form is not part of the MVP. In Phase 1, admin manually creates and edits leader and member records via the admin portal. The self-service leader form ships in Phase 2.

```plaintext
1. Leader opens /leader.html → Google Sign-In (one-tap if already signed in)
2. Frontend calls GET /api/leaders/me with JWT
3. Cloud Run looks up record by google_uid → returns full profile + groups + members
4. Form pre-fills:
   Section 1 — Personal Info (all Member/Intern fields)
   Section 2 — Groups Led (one card per group, type + member list)
   Section 3 — Interns (confirmed interns shown with ✅, pending shown with clock icon)
5. Leader updates any fields, adds/removes members → submits
6. POST /api/submit → writes to victory_bronze.raw_form_submissions
7. Success message: "Thank you, your data has been received."
8. Form resets
```
### VG Leader Form — Sections

```plaintext
┌─────────────────────────────────────────┐
│  SECTION 1 — Personal Information       │
│  First Name · Middle Name · Last Name   │
│  Suffix · Birthday · Address            │
│  Gender · Civil Status                  │
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
- Adding an intern via form creates a new `victory_silver.intern_relationships` record with `review_status = 'pending'` and `source = 'leader_form'`. Admin confirms in the admin portal.
- Removal of interns is admin-managed only (not via form). Leaders cannot remove interns through the form — they communicate removals to admin directly.

**Section 2 — Victory Group member auto-removal:** When a leader re-submits the form, the Dataform pipeline compares the new member list against the current active members in Silver. Any member who was previously active (`is_active = TRUE`) but is absent from the new submission is automatically set to `is_active = FALSE` on the next scheduled run. Leaders do not explicitly "remove" members — omitting them from the submission is the removal signal.

**Section 1 — Employment conditional fields display:** When `employment_type = 'employed'` is selected, show `nature_of_work` + `company_name` fields only. When `employment_type = 'self_employed'`, show `nature_of_business` + `business_name` fields only. Both field pairs are mutually exclusive — the inapplicable pair is hidden and cleared on switch (Alpine.js `x-show` directive).

### Admin Review Queue — Phase 2 Additions

> **Phase 2 tabs (Tabs 3–5)** activate when the VG Leader form ships. Full queue specification — including the Tab 1 interaction spec, duplicate resolution rules, and the complete queue layout — is in [UX_FLOWS_PHASE1.md — Admin Review Queue](UX_FLOWS_PHASE1.md#admin-review-queue).

**Phase 2 additions:**
- **Tab 3 — Unresolved Interns:** `intern_relationships` records where `intern_person_id = NULL`. Name typed by a leader but could not be auto-matched. Admin links or creates a new Contact record.
- **Tab 4 — Interns Without Active Relationship:** Persons with `journey_stage = 'intern'` but no approved, active `intern_relationships` record.
- **Tab 5 — Unlinked VG Members:** `victory_group_members` records where `person_id IS NULL` and `is_active = TRUE`. Leader submitted a member name not yet linked to a system person record.

### Pastoral Event Self-Registration Flow (`pastoral_self` category) — Phase 3

> **Phase 1 scope:** Pastoral event registration is **admin-initiated only** in Phase 1. Admin registers celebrants and registrants directly via the admin portal (`/events.html`). The public self-registration flow below is deferred to Phase 3.

> **Phase 1 — Admin-initiated pastoral events:** Both `pastoral_self` and `pastoral_admin` categories are admin-managed in Phase 1. Admin creates the event via `POST /api/events` (selecting the appropriate `event_type_id` from `victory_silver.event_type_catalog`), then adds registrations manually via the event's registrations view in `/events.html`. For `pastoral_admin` events (`is_sensitive = TRUE`, e.g. funerals), the event is not displayed publicly — admin enters family members as new Contact-stage persons via `POST /api/persons` and links them as registrations. See [docs/EVENTS.md](EVENTS.md) for the full `pastoral_admin` category definition.

Applies to Weddings, Child Dedications, and Business Dedications. These events have public pages at `/e/[slug]` but use a different form from the standard event registration.

> **Key difference from standard events:** The person signing in (the registrant) is NOT the celebrant. The celebrant(s) are new Contact-stage person records captured via the form.

```plaintext
1. Person opens /e/[slug] for a pastoral_self event (e.g. Wedding Dedication).
2. Google Sign-In (the registrant — the person requesting the pastoral service).
3. GET /api/events/{slug}/pre-check → verifies event is registration_open.
4. Frontend detects event.category = 'pastoral_self' → shows PASTORAL FORM instead of
   standard event registration form:

   ┌─────────────────────────────────────────┐
   │  [Event Name] — e.g. Wedding Dedication │
   │  📅 [Date] · 📍 [Venue]               │
   │                                         │
   │  SECTION 1 — About the Celebrant(s)     │
   │  (The person(s) being dedicated/wed)    │
   │                                         │
   │  For Wedding:                           │
   │    Groom Full Name:   [___________]     │
   │    Bride Full Name:   [___________]     │
   │                                         │
   │  For Child Dedication:                  │
   │    Child Full Name:   [___________]     │
   │    Parent(s) Name:    [___________]     │
   │                                         │
   │  For Business Dedication:               │
   │    Business Name:     [___________]     │
   │    Owner Full Name:   [___________]     │
   │                                         │
   │  SECTION 2 — Your Contact Info          │
   │  (The person registering)               │
   │    Name:       [auto from Google]       │
   │    Contact #:  [___________]            │
   │                                         │
   │         [ Submit Registration ]          │
   └─────────────────────────────────────────┘

5. Submit → Backend:
   a. For each celebrant name entered: search victory_silver.persons by full name
      (case-insensitive). No match → create new Contact-stage person record
      (source = 'pastoral_event', review_status = 'pending').
   b. Create event_registration linking the registrant's person_id
      (from their Google account). The celebrant's name is stored
      in primary_person_name as a display string. If a Silver person record
      was created or matched for the celebrant, they may also be linked
      via a separate registration record.
   c. Write to victory_bronze.raw_event_actions (action_type = 'registered').
6. SUCCESS SCREEN (clean confirmation — no payment instructions).
```

**Note on `primary_person_name`:** The `event_registrations.primary_person_name` STRING field captures the celebrant's name as a display string for pastoral events. Admin can view this in the event attendee list.

---

### Admin Portal — Person Record View: Special States

#### Pre-Dataform Banner (VG Leader Record, Groups Not Yet Loaded)

> **Phase 2.** This banner only appears after the VG Leader form ships. It bridges the gap between a leader's first form submission and the next Dataform pipeline run.

When a VG Leader submits their form for the first time, their Victory Groups are written to Bronze and appear in Silver only after the next Dataform run (up to 1 hour). If the admin opens the person's record before that run completes, the Groups section will be empty.

```plaintext
┌──────────────────────────────────────────────────────────────────┐
│  ⏳  Victory Groups Pending                                       │
│  Groups submitted in this form are being processed and will       │
│  appear within 1 hour (next scheduled pipeline run).             │
│  You can proceed with Step 2 (Approve this record) now.          │
└──────────────────────────────────────────────────────────────────┘
```

- **Trigger:** A `victory_bronze.raw_form_submissions` record exists with `source_page = 'leader'` for this person AND no linked `victory_silver.victory_groups` records exist for this person yet.
- **Location:** Inline banner at the top of the Groups section on the person record view.
- **Action available:** Admin may still proceed to approve the person record in Step 2 — groups not being visible yet does not block this step.

> Phase 1 special states (Data Inconsistency Warning and Member Stage Soft-Warning) are in [UX_FLOWS_PHASE1.md — Admin Portal Special States](UX_FLOWS_PHASE1.md#admin-portal--person-record-view-special-states).

---

### VG Leader Promotion — Intern Closure Inline Prompt (Step 5)

> **Phase 2 (full flow). Phase 1 (button only).**
>
> The **"Promote to VG Leader" button** and Phase 1 button scope are documented in [UX_FLOWS_PHASE1.md — VG Leader Promotion](UX_FLOWS_PHASE1.md#vg-leader-promotion--phase-1-scope).
>
> The **standard 5-step promotion workflow** (Step 1: person submits VG Leader form → Step 2: admin approves → Steps 3–4: promote → Step 5: close intern relationship) is Phase 2, because Step 1 requires the VG Leader form. The intern closure prompt below only appears when `intern_relationships` records exist (Phase 2).

Immediately after admin clicks **[ Promote to VG Leader ]** and the atomic action completes, Cloud Run checks for any active `intern_relationships` records (`is_active = TRUE`) where `intern_person_id = <this person>`.

```plaintext
┌──────────────────────────────────────────────────────────────────┐
│  ℹ️  Active Intern Relationship Found                             │
│                                                                  │
│  This person has an active intern relationship with              │
│  [Supervising Leader Name].                                      │
│  Close it now?                                                   │
│                                                                  │
│  [ Close Relationship ]          [ Dismiss ]                     │
│                                                                  │
│  Closing sets is_active = FALSE and end_date = today             │
│  via PATCH /api/intern-relationships/{id}.                       │
│  If dismissed, this open relationship is re-surfaced             │
│  as a warning on the person's record view until resolved.        │
└──────────────────────────────────────────────────────────────────┘
```

- **If not found:** No prompt. Promotion flow completes silently.
- **Trigger:** `POST /api/persons/{id}/promote-to-leader` response includes:
  - `has_active_intern_relationship: true/false` — renders the prompt when `true`
  - `active_intern_relationship_id: "uuid | null"` — the relationship ID used as target for
    `PATCH /api/intern-relationships/{id}` when admin clicks [ Close Relationship ]
- **If dismissed:** A persistent warning banner appears on the person's record view: *"This person has an unclosed intern relationship with [Leader Name]. [ Close Relationship ]"* — re-surfaced on every admin view until resolved.

---

### Group & Member Lifecycle Management (Admin Portal)

> **Phase 2.** Victory Group and member lifecycle management (deactivating groups, removing members) activates once the VG Leader form is live and group records are populated via leader submissions.

#### Deactivating a Victory Group

- **Trigger:** Admin navigates to a leader's record → Groups section → selects a group → clicks `[ Deactivate Group ]`.
- **Backend:** `PATCH /api/victory-groups/{id}` with `{ "is_active": false }`. SCD2 closes the `victory_groups` record (`valid_to = NOW()`, `is_current = FALSE`, `is_active = FALSE`). All active members in that group are also set to `is_active = FALSE`, `removed_at = NOW()`.
- **Effect:** The group disappears from the leader's dashboard and from `vw_victory_group_summary` active group counts.

#### Removing a VG Member

- **Trigger:** Admin navigates to a leader's record → Groups section → member row → clicks `[ Remove Member ]`.
- **Backend:** `PATCH /api/vg-members/{id}` with `{ "is_active": false }`. Direct UPDATE on `victory_group_members`: `is_active = FALSE`, `removed_at = NOW()`.
- **Note:** This is distinct from `PATCH /api/vg-members/{id}/link`, which links a `person_id` to an unlinked member name. Removal and linking are separate operations.

---

### Admin Stage Transition Actions — Phase 2

> Phase 1 stage transitions (CONTACT→MEMBER two-call pattern, MEMBER→VG LEADER direct path) are in [UX_FLOWS_PHASE1.md — Admin Stage Transition Actions](UX_FLOWS_PHASE1.md#admin-stage-transition-actions-person-record-view--phase-1).

```plaintext
── Phase 2 transitions (not available in Phase 1) ──────────────────────────
MEMBER → VG INTERN → VG LEADER  (Phase 2 full lifecycle path)
  The intern stage and all intern_relationships management ship with the
  VG Leader form in Phase 2.
```

### Admin Class Roster Management (`/admin.html` — Equipping Classes)

> **Phase 2.** Equipping class batch creation and enrollment management is not required for the event registration and member profile MVP. Ships in Phase 2 alongside the VG Leader form and leader dashboard.

Key admin flows for managing equipping class batches and enrollments:

```plaintext
1. Admin creates a class batch:
   POST /api/equipping-classes
   Fields: canonical_step (spiritual_foundations|leadership_113|...),
           class_name (e.g. "Spiritual Foundations Batch 12"),
           batch_code, facilitator_person_id, start_date, end_date, capacity.

2. Admin enrolls persons in the class:
   POST /api/equipping-enrollments
   Fields: class_id + person_id (found via GET /api/persons?q=<name>).
   Creates record with enrollment_status = 'enrolled'.

3. Class session occurs — admin marks attendance:
   POST /api/events/{id}/attend (for the equipping class event)
   → triggers discipleship pipeline → updates enrollment_status = 'completed'.

4. Admin corrects enrollment status (if needed):
   PATCH /api/equipping-enrollments/{id}
   E.g. enrollment_status = 'dropped' with drop_reason.
```



---

*Owner: @architect. Last updated: 2026-02-25. Phase 1 flows split to UX_FLOWS_PHASE1.md (2026-02-25). This file covers Phase 2–4 flows and the full page/delivery overview.*
