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
| `/reports.html` | Executives | Looker Studio embed or direct link | **Phase 4** | Embedded Looker Studio dashboards. No data editing. |
### Mobile Responsiveness Strategy

- Bootstrap 5 grid provides mobile-first responsiveness for the existing member form.
- Build with Bootstrap breakpoints: `xs` (320px+), `sm` (576px+), `md` (768px+), `lg` (992px+).
- Test on real devices using Google AntiGravity's preview capabilities or BrowserStack free tier.
- Touch targets: minimum 44×44px for all interactive elements per WCAG 2.1.
- Font sizes: minimum 16px body text to prevent iOS auto-zoom on form fields.
- Viewport meta tag enforced: `width=device-width, initial-scale=1.0`.

### Event Page Design

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


## UX Flows
### Entry Points Summary

| Entry Point | URL | Who | Auth | Key Behavior | Phase |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Event Landing Page | `/e/[slug]` | Anyone | Google Sign-In | Smart pre-check → profile form or confirm or already-registered screen. VG question for new users. | **Phase 1** |
| Member Profile | `/profile` | VG Members | Google Sign-In | View and update own record. Pre-fills from Silver. Collects employment info and VG Leader name (member-stage required fields). Cannot see other records. | **Phase 1** |
| Admin Portal | `/admin` | Admin team | Google Sign-In + admin role | Review queue, event management, person editing, role assignment. | **Phase 1** |
| VG Leader Form | `/leader` | VG Leaders | Google Sign-In | New → blank form. Returning → full pre-fill. Captures personal info + groups + members. | **Phase 2** |
| Pastoral Event Page | `/e/[slug]` | Families / couples | Google Sign-In | Simplified public self-registration for pastoral events (Weddings, Dedications). Admin-initiated in Phase 1. | **Phase 3** |
| Reports | `/reports` | Executives | Google Sign-In + executive role | Embedded Looker Studio dashboards. No data editing. | **Phase 4** |

### Member Profile Form — `/profile.html`

> **Account-Claiming (admin-created records):** On every page that calls `GET /api/me`, if no record matches by `google_uid`, Cloud Run automatically attempts an email-match fallback against `persons WHERE google_uid IS NULL`. If a match is found, the `google_uid` is claimed silently and the form pre-fills normally. If no email match is found, the user sees: *"Your profile was not found. Please ask your Victory Group leader or admin to create your profile."* — no form is shown.

> **Stage-dependent Facebook enforcement:** If the user's `journey_stage = 'contact'`, the Facebook field is shown with an "encouraged" label and is not required. If `journey_stage = 'member'` or higher, Facebook is **required** — the form submission is blocked until it is filled.

```plaintext
1. Member opens /profile → Google Sign-In (one-tap if already signed in)
2. Frontend calls GET /api/me with JWT
3. Cloud Run looks up record by google_uid → returns full profile.
   If no match by google_uid, Cloud Run attempts email-match fallback (account-claiming).
   If still no match → show "Profile not found" message, no form displayed.
4. Form pre-fills all known fields:
   Section 1 — Personal Info (Contact-stage fields, all read-only if already complete)
   Section 2 — Employment Info (Employment Type → conditional fields)
   Section 3 — VG Leader (their leader's first and last name)
5. Member updates or completes fields → submits
6. POST /api/submit → writes to victory_bronze.raw_form_submissions
7. Success message: "Thank you, your profile has been updated."
```

**Field display rules:**
- All Contact-stage fields (name, address, contact number, birthday, Facebook) are shown pre-filled and editable — members may correct their own data.
- Employment Type and conditional fields (Section 2) are always shown — these are the primary reason a member visits this page.
- VG Leader name fields (Section 3) are shown pre-filled if previously set and editable — the member may update if their leader changes.
- A member cannot view or edit any other person's record. The form is scoped strictly to `google_uid` of the signed-in user.

**Write path:** Identical to the VG Leader form — all updates write to `victory_bronze.raw_form_submissions` with `source_page = 'profile'`. Dataform reconciles on the next scheduled run (SCD2 upsert on `victory_silver.persons` and `victory_silver.person_occupations`).

---

### VG Leader Form — Returning User Flow

> **Phase 2.** The VG Leader form is not part of the MVP. In Phase 1, admin manually creates and edits leader and member records via the admin portal. The self-service leader form ships in Phase 2.

```plaintext
1. Leader opens /leader → Google Sign-In (one-tap if already signed in)
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

### Event Registration Flow — Complete Decision Tree

> **Facebook field — stage-aware enforcement:** Facebook Profile is non-blocking for event registration by Contact-stage persons. The pre-check endpoint does not include `facebook_profile` in `missing_fields` and does not affect `profile_complete` for persons with `journey_stage = 'contact'`. For persons at `journey_stage = 'member'` or higher, Facebook is required and will appear in `missing_fields` if absent.

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
   │ "Already     │  │  victory_silver.persons?           │
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
     Step 1 (immediate, synchronous):
       a. Cloud Run writes full profile to victory_bronze.raw_form_submissions (standard write-path).
       b. Cloud Run immediately creates a minimal Silver person record directly:
          person_id (new UUID), google_uid, first_name, last_name,
          review_status = 'pending', source = 'event_registration',
          journey_stage = 'contact', is_current = TRUE, valid_from = NOW().
          This is the only permitted direct Silver write from Cloud Run — required so that
          the event registration FK (person_id) can be resolved without waiting for Dataform.
       c. Cloud Run creates victory_silver.event_registrations using the new person_id.
       d. SUCCESS SCREEN returned to user immediately.
     Step 2 (async, next scheduled Dataform run):
       Dataform stg_persons.sqlx processes the victory_bronze.raw_form_submissions record and
       SCD2-upserts the full Silver person record (adding all remaining fields from the
       form payload). The existing minimal record is updated in-place — no duplicate created.
7. SUCCESS SCREEN (clean confirmation — no payment instructions)
```

> **Write-path exception:** Cloud Run normally writes only to Bronze. The two-phase write above is the single permitted exception: a minimal Silver record is created immediately to satisfy the `event_registrations.person_id` FK and provide an instant confirmation. The Dataform pipeline then reconciles the full record on its next run. All new Bronze submissions must exist before the Silver minimal record is created — Bronze is always the authoritative source.

### Scenario 2 — Returning Person, Complete Profile, NOT Registered

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

> *This scenario assumes the returning person is at `journey_stage = 'member'` or higher — which is why `facebook_profile` appears in `missing_fields` as a required field.*

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
     a. Cloud Run writes updated profile fields to victory_bronze.raw_form_submissions.
     b. The person already has a Silver record (person_id known from pre-check).
        Cloud Run creates victory_silver.event_registrations immediately using the existing person_id —
        no direct Silver write needed. The person_id FK is already resolved.
     c. Dataform reconciles the profile update on the next scheduled run (SCD2 upsert adds missing fields).
     d. SUCCESS SCREEN returned to user immediately — no re-registration step required.
7. SUCCESS SCREEN (clean confirmation — no payment instructions)
```

### Success Screen — All Scenarios
The success screen is intentionally minimal. No payment instructions, no GCash numbers, no bank transfer details are shown on this screen.
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

> **Phase 1:** Tab 1 (Pending Records) and Tab 2 (Duplicates) are required for MVP — all public event registrations and admin-created records flow through here.
> **Phase 2:** Tab 3 (Unresolved Interns), Tab 4 (Interns Without Active Relationship), and Tab 5 (Unlinked VG Members) activate when the VG Leader form ships in Phase 2.

Every record created by a public form or admin direct entry starts as `review_status = 'pending'`. The admin portal surfaces these records in a dedicated view.

The admin review queue is organized into tabs, each surfacing a distinct category of records requiring action.

> **Queue routing rule — Pending + Duplicate:** Records with both `review_status = 'pending'` AND `duplicate_flag = TRUE` appear **in Tab 2 only (Duplicates)**. They do NOT appear in Tab 1. This prevents admin from inadvertently approving a duplicate record before the duplicate is resolved. Once the duplicate is resolved (one record kept, one rejected), the kept record returns to Tab 1 if its `review_status` is still `pending`.

```plaintext
┌──────────────────────────────────────────────────────────────────┐
│  ADMIN REVIEW QUEUE                                              │
│  [ Pending Records (2) ] [ Duplicates (1) ]                      │
│  ── Phase 2 tabs ──────────────────────────────────────────    │
│  [ Unresolved Interns (1) ] [ Interns Without Relationship (1) ] │
│  [ Unlinked VG Members (3) ]                                     │
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
│  Full merge is deferred to Phase 5.                              │
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
│  TAB 3 — UNRESOLVED INTERNS (Phase 2)                           │
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
│  TAB 4 — INTERNS WITHOUT ACTIVE RELATIONSHIP (Phase 2)          │
│  Persons with journey_stage = 'intern' but no approved,          │
│  active intern_relationships record.                             │
│                                                                  │
│  [ Ben Cruz ]  Stage: intern  No active relationship found       │
│  [ View Pending Relationships ] [ Create Relationship ]          │
│                                                                  │
│  ────────────────────────────────────────────────────────────    │
│                                                                  │
│  TAB 5 — UNLINKED VG MEMBERS (Phase 2)                          │
│  victory_group_members records where person_id IS NULL           │
│  and is_active = TRUE. Leader submitted a member name that       │
│  has not yet been linked to a system person record.              │
│                                                                  │
│  [ "Anna Reyes" ]  Group: Group 1  Leader: Maria Clara           │
│  Search: [_______________] → [ Link to Person ]                  │
│  [ Create New Contact Record ]  [ Leave Unlinked ]               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Duplicate resolution rules (Phase 1):**
- Admin reviews both records side by side and selects which to keep as the canonical record.
- The kept record retains its `person_id`, `google_uid`, and all history.
- The rejected record is set to `review_status = 'rejected'` and `duplicate_of_person_id = <canonical_person_id>`. It is excluded from all Gold view reporting.
- The rejected record's event registrations and history are **not merged** in Phase 1 — they are excluded from counts. Full merge with history re-attribution is deferred to Phase 5 (see Implementation Phases in ARCHITECTURE.md).
- Once a record is rejected as a duplicate, it is removed from the Duplicates tab and surfaced in a separate "Rejected Records" audit view accessible to admin only.

### Pastoral Event Self-Registration Flow (`pastoral_self` category) — Phase 3

> **Phase 1 scope:** Pastoral event registration is **admin-initiated only** in Phase 1. Admin registers celebrants and registrants directly via the admin portal (`/events.html`). The public self-registration flow below is deferred to Phase 3.

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

Three UI states on the admin person record view require explicit specification.

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

#### Data Inconsistency Warning (Role / Stage Mismatch)

A person should have `journey_stage = 'leader'` if and only if they have an active `vg_leader` role in `victory_silver.person_roles`. If these are out of sync (e.g., due to a legacy data import or a failed promotion transaction), the admin portal surfaces a warning.

```plaintext
┌──────────────────────────────────────────────────────────────────┐
│  ⚠️  Data Inconsistency Detected                                  │
│  This person's role and journey stage do not match.              │
│                                                                  │
│  Role:          vg_leader (active)                               │
│  Journey Stage: member                                           │
│                                                                  │
│  Use the Promote action to resolve this mismatch.               │
│  [ Promote to VG Leader ]                                        │
└──────────────────────────────────────────────────────────────────┘
```

- **Trigger (Role ahead of Stage):** `person_roles` contains an active `vg_leader` row AND `persons.journey_stage ≠ 'leader'`.
- **Trigger (Stage ahead of Role):** `persons.journey_stage = 'leader'` AND no active `vg_leader` row in `person_roles`.
- **Location:** Inline warning banner at the top of the person record view.
- **Action:** `[ Promote to VG Leader ]` button calls `POST /api/persons/{id}/promote-to-leader` (idempotent — re-running it corrects both fields atomically).

#### Member Stage Soft-Warning (VG Leader Name Missing) — Phase 1

When admin sets `journey_stage = member` on a person record, the portal immediately checks whether `vg_leader_first_name` and `vg_leader_last_name` are populated.

```plaintext
┌──────────────────────────────────────────────────────────────────┐
│  ⚠️  VG Leader Name Missing                                       │
│                                                                  │
│  This member's VG Leader name has not been recorded.             │
│  Please collect and enter it, or ask the member to update        │
│  their profile at /profile.html.                                 │
│                                                                  │
│  [ Edit Record ]                              [ Dismiss ]        │
└──────────────────────────────────────────────────────────────────┘
```

- **Trigger:** Admin sets `journey_stage = 'member'` AND (`vg_leader_first_name` IS NULL OR `vg_leader_last_name` IS NULL).
- **Location:** Inline soft-warning displayed immediately after the stage transition is saved. Does **not** block the transition — admin may proceed.
- **Effect of leaving unresolved:** The record's `profile_completeness_pct` in admin views will remain low until the VG Leader name fields are populated, either by admin directly or by the member via `/profile.html`.
- **Resolution paths:** (1) Admin edits the record directly via the admin portal. (2) Member visits `/profile.html`, which pre-fills Section 3 (VG Leader name) for them to complete and submit.

---

### VG Leader Promotion — Intern Closure Inline Prompt (Step 5)

> **Phase 2 (full flow). Phase 1 (button only).**
>
> The **"Promote to VG Leader" button** is available in Phase 1 on any person's admin record view — admin can directly promote without requiring a form submission. This is how Phase 1 handles early data setup (admin creates person records manually and promotes directly).
>
> The **standard 5-step promotion workflow** (Step 1: person submits VG Leader form → Step 2: admin approves → Steps 3–4: promote → Step 5: close intern relationship) is Phase 2, because Step 1 requires the VG Leader form. The intern closure prompt below only appears when `intern_relationships` records exist (Phase 2).
>
> The **Data Inconsistency Warning** (role/stage mismatch) is Phase 1 — it surfaces the promote button as a repair action regardless of whether the form was submitted.

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
- **Trigger:** `POST /api/persons/{id}/promote-to-leader` response includes `has_active_intern_relationship: true/false` flag. Frontend renders the prompt when `true`.
- **If dismissed:** A persistent warning banner appears on the person's record view: *"This person has an unclosed intern relationship with [Leader Name]. [ Close Relationship ]"* — re-surfaced on every admin view until resolved.

---

### Event Attendance (Post-Event Admin Action)

Attendance for all events (paid or free) is recorded by admin after the event concludes — not at the venue door. Admin marks who attended via the admin portal after the event.

```plaintext
1. Event concludes.
2. Admin opens /events.html → selects the event → clicks [ View Registrations ].
3. For each person who attended: Admin clicks [ Mark Attended ].
   Backend calls POST /api/events/{id}/attend with person_id.
   This writes attendance to Bronze → Dataform creates event_attendances.
   event_registrations.status is updated to 'attended' in-place.
4. For registrants who did not attend: Admin sets status = 'no_show'
   via PATCH /api/event-registrations/{id}.
5. *(Phase 2+)* Discipleship pipeline triggers enrollment completion for persons
   with a matching equipping enrollment (see Discipleship Auto-Pipeline in API.md).
   No-op in Phase 1 — equipping enrollments do not exist until Phase 2.
```

Payment status fields (`payment_status`, `payment_ref`, `amount_paid`, `payment_method`) are available on `event_registrations` for admin reference. They are not part of a documented Phase 1 process flow. Payment details are communicated through existing church channels (social media, announcements).


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

### Admin Stage Transition Actions (Person Record View) — Phase 1

These are direct admin actions on a person's record view that drive stage progression. They are not surfaced via a queue — admin navigates to the person record and acts manually.

```plaintext
CONTACT → MEMBER  (Phase 1)
  Trigger: Leader verbally confirms One2One is complete.
  Admin action:
    1. Navigate to person record.
    2. Check ✅ "One2One Completed" — sets one2one_completed = TRUE, one2one_date = today.
    3. Update Journey Stage → "Member" — sets journey_stage = 'member'.
       (Soft-warning appears if vg_leader_first_name / last_name is missing — see above.)

MEMBER → VG LEADER  (Phase 1 direct path)
  In Phase 1, admin promotes a Member directly to VG Leader — no intern stage required.
  Admin action: Click [ Promote to VG Leader ] on the person record view.
  See VG Leader Promotion section below for the full flow and phase breakdown.

── Phase 2 transitions (not available in Phase 1) ──────────────────────────
MEMBER → VG INTERN → VG LEADER  (Phase 2 full lifecycle path)
  The intern stage and all intern_relationships management ship with the
  VG Leader form in Phase 2.
```

---

### Admin Event Management (`/events.html`)

Key admin actions on event records (all via `PATCH /api/events/{id}` unless noted):

```plaintext
Admin actions:
  ┌──────────────────────────────────────────────────────────────────┐
  │  EVENT: Date Talk — February 2025                                │
  │  Status: registration_open  ·  Capacity: 200 (informational)    │
  │                                                                  │
  │  [ Open Registration ]    → status = registration_open          │
  │  [ Close Registration ]   → status = closed                     │
  │  [ Mark Completed ]       → status = completed                  │
  │  [ Cancel Event ]         → status = cancelled                  │
  │                                                                  │
  │  Hero image:  [ Upload Image ]  (sets hero_image_url)           │
  │  Capacity:    [ Edit ]          (informational only — no enforcement) │
  │                                                                  │
  │  [ View Registrations ]   → lists all event_registrations       │
  │  [ Mark Attended (post-event) ] → POST /api/events/{id}/attend  │
  └──────────────────────────────────────────────────────────────────┘
```

- Creating a new event: `POST /api/events` (fields: event_type_id, event_name, start_datetime, end_datetime, venue_name, capacity, is_paid, price, page_slug — auto-generated if not provided).
- `capacity` is displayed for admin planning reference. It does NOT block registration when reached (Phase 1).
- All status transitions are manual admin actions — no auto-transitions.

---

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

*Owner: @architect. Last updated: 2026-02-24. Delivery phases established: Phase 1 MVP scope locked to `/e/[slug]`, `/profile`, `/admin`, `/events`.*
