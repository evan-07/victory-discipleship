# Gold Views — Reporting Layer

← Part of [ARCHITECTURE.md](../ARCHITECTURE.md) | See also: [SCHEMA.md](SCHEMA.md) · [DATA_PIPELINE.md](DATA_PIPELINE.md) · [SECURITY.md](SECURITY.md)

---

## Gold Views — Reporting Layer

All Gold views are read-only SQL views on BigQuery. Row access policies are enforced at the database engine level — not the application layer.

> **Binding rule — `review_status` filter:** Every Gold view that joins `victory_silver.persons` **MUST** include the filter `WHERE persons.review_status != 'rejected'`. This is non-negotiable. Rejected records are duplicate persons that have been superseded by a canonical record — including them in any count, funnel, or engagement metric produces inflated and incorrect reporting. This filter is enforced via a Dataform assertion on each Gold SQLX file. Any Gold view missing this filter will fail the CI/CD quality gate.
>
> **Pending vs. approved in Gold views:** `pending` records (new submissions awaiting admin review) are included in Gold views by default so that newly registered event attendees and form submitters appear in reporting immediately. Only `rejected` records are excluded.

| View Name | Audience | Description |
| :--- | :--- | :--- |
| `victory_gold.vw_member_demographics` | Executive + Admin | Total members, gender split, age bands, marital status, occupation breakdown (employed vs. self-employed), journey stage counts, monthly new member trend. |
| `victory_gold.vw_equipping_funnel` | Executive + Admin | High-level funnel: counts per step for old and new pathway. Completion rates. "Encouraged SF" count. Drill-down: individuals at each stage with name, journey stage, and days since last completed step. |
| `victory_gold.vw_equipping_completion` | Admin | One row per person. Boolean flags for each canonical step. Completion status for old pathway, new pathway, and combined. encouraged_to_add_sf flag. Used for follow-up targeting. |
| `victory_gold.vw_equipping_cohorts` | Admin | Per-batch: enrolled vs. completed vs. dropped, completion rate, facilitator, batch dates. Cohort tracking — who went through a class together. |
| `victory_gold.vw_event_participation` | Executive + Admin | Per-event: registered, attended, no-show, attendance rate, revenue collected vs. expected. Filters out is_sensitive events from executive view. |
| `victory_gold.vw_attendance_headcounts` | Executive + Admin | Overall anonymous headcount tracking for Sunday Services and general events over time. |
| `victory_gold.vw_person_engagement` | Executive + Admin | Per person: total events attended, events in last 12 months, unique event types, first event date, most recent event date, engagement consistency score. |
| `victory_gold.vw_person_event_history` | Admin + Leader (filtered) | Full chronological event timeline per person. Equipping classes shown separately from general events. Sensitive events excluded for non-admin. |
| `victory_gold.vw_victory_group_summary` | Executive + Admin | Group count by type (single, wives, husbands, students, young_pro). Leader leaderboard. Member count per group. Intern counts. Groups with zero members flagged. |
| `victory_gold.vw_leader_dashboard` | VG Leader | Row-level filtered by leader_email = SESSION_USER(). Own groups, member list per group, own equipping completion status, own event history, own ministry affiliations. |
| `victory_gold.vw_ministry_participation` | Executive + Admin | Active vs. interested per ministry, monthly join trend, multi-ministry members. |
| `victory_gold.vw_pastoral_events` | Admin only | All pastoral events including sensitive ones. Family contacts created. Follow-up status. Excluded from executive Looker Studio entirely. |
| `victory_gold.vw_admin_full` | Admin only | Denormalized join of all silver entities. Includes journey_stage, review_status, duplicate_flag, equipping completion flags, engagement score, employment info, VG membership, and group leadership details. |
| `victory_gold.vw_business_network` | Admin only | Purpose-built view for the Business & Professionals Network dashboard. Joins `victory_silver.persons` + `victory_silver.person_occupations` (is_current = TRUE). Exposes only: person_id, first_name, last_name, employment_type, nature_of_work, company_name, nature_of_business, business_name. Filtered to employed and self_employed records only. |

## Gold View Dependency DAG

All Gold views in this system read exclusively from Silver tables — there are **zero Gold-on-Gold view dependencies**. Any future Gold-on-Gold chain MUST be reviewed by `@architect` and documented in [DECISIONS.md](DECISIONS.md) before implementation.

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

---

*Owner: @architect. Last updated: 2026-02-24.*
