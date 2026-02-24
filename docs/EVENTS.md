# Event Taxonomy

← Part of [ARCHITECTURE.md](../ARCHITECTURE.md) | See also: [UX_FLOWS.md](UX_FLOWS.md) · [SCHEMA.md](SCHEMA.md)

---

## Event Taxonomy

Four distinct categories in `victory_silver.event_type_catalog`. Adding a new event type is always a single admin `INSERT` — zero code changes.

### Category Definitions

#### 🎓 Equipping Pathway

- **Examples:** Victory Weekend, Spiritual Foundations, Discipleship Class, Leadership 113
- **Registration:** Admin-managed class roster only. No public landing page. No self-registration.
- **Data entry:** Admin creates class batch, manages enrolled → completed / dropped.
- **Profile impact:** Completion updates `victory_silver.equipping_enrollments`. Gold views compute pathway progress.
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

### `victory_silver.event_type_catalog` Category Values

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

---

*Owner: @architect. Last updated: 2026-02-24.*
