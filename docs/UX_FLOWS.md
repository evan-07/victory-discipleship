# Frontend & UX Flows

← Part of [ARCHITECTURE.md](../ARCHITECTURE.md) | See also: [API.md](API.md) · [JOURNEY_STAGES.md](JOURNEY_STAGES.md) · [EVENTS.md](EVENTS.md)

---

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
6. POST /api/submit → writes to victory_bronze.raw_form_submissions
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
- Adding an intern via form creates a new `victory_silver.intern_relationships` record with `review_status = 'pending'` and `source = 'leader_form'`. Admin confirms in the admin portal.
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
       a. Cloud Run writes full profile to victory_bronze.raw_form_submissions (standard write-path).
       b. Cloud Run immediately creates a minimal Silver person record directly:
          person_id (new UUID), google_uid, first_name, last_name,
          review_status = 'pending', source = 'event_registration',
          journey_stage = 'contact', is_current = TRUE, valid_from = NOW().
          This is the only permitted direct Silver write from Cloud Run — required so that
          the event registration FK (person_id) can be resolved without waiting for Dataform.
       c. Cloud Run creates victory_silver.event_registrations using the new person_id.
       d. SUCCESS SCREEN returned to user immediately.
     Phase 2 (async, next Dataform run):
       Dataform stg_persons.sqlx processes the victory_bronze.raw_form_submissions record and
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
3. Backend auto-creates victory_silver.event_registrations:
     status = 'registered', registration_source = 'admin'
     payment_status = 'pending' (paid events) | 'N/A' (free events)
     registered_at = check_in_timestamp
4. Backend immediately writes attendance to victory_bronze.raw_event_actions.
5. Admin can subsequently update payment_status (paid / waived) and enter Reference # as needed.
6. Admin can also override walk-in registration details or create the registration entry manually
   before check-in if they prefer explicit control.
```

No payment gateway in Phase 1. All payment confirmation is manual. Payment instructions are never displayed on the registration success screen.



---

*Owner: @architect. Last updated: 2026-02-24.*
