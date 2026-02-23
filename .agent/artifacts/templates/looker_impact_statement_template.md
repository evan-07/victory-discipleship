---
artifact_type: template
name: Looker Impact Statement
owner: "@data-engineer + @bi-analyst"
required_for: "Any change to data/definitions/3_gold/**"
gate: "Must be completed and @bi-analyst approved before @orchestrator can pass the Architect Gate"
---

# Looker Impact Statement

> **Instructions:** Copy this template to `.agent/artifacts/current_looker_impact_<branch>.md` and fill in all sections before submitting a PR that modifies `data/definitions/3_gold/**`.

**Date:** <!-- YYYY-MM-DD -->
**PR Branch:** <!-- e.g. feature/add-engagement-score -->
**Author:** @data-engineer
**Reviewed by:** @bi-analyst _(required before merge — see Sign-off section below)_

---

## Change Summary

<!-- One paragraph describing what is changing in the Gold layer and why. -->

---

## Affected SQLX Files

<!-- List every .sqlx file being added, modified, or removed. -->
- `data/definitions/3_gold/gold_XXXX.sqlx` — _Added / Modified / Removed_

---

## Looker Studio Dashboards & Reports Impacted

| Dashboard / Report Name | Data Source View | Impact Type | Action Required |
|---|---|---|---|
| <!-- e.g. Member Demographics --> | `vw_member_demographics` | None / Breaking / Non-breaking | <!-- e.g. Update date dimension field --> |

> **Impact Types:**
> - **None** — No Looker charts reference the changed fields.
> - **Non-breaking** — New fields added; existing fields unchanged. Charts still work but may benefit from updates.
> - **Breaking** — Fields removed or renamed. Existing Looker charts will fail unless updated by `@bi-analyst`.

---

## Schema Delta

| Field | Action | Data Type | Breaking? | Looker Action Required |
|---|---|---|---|---|
| `field_name` | Added / Removed / Renamed from `old_name` | STRING / INT64 / BOOL / NUMERIC / DATE / TIMESTAMP | Yes / No | <!-- e.g. Remove from chart, update dimension --> |

---

## Compatibility Assessment

- [ ] No existing Looker charts reference removed or renamed fields
- [ ] New fields are additive (non-breaking to existing dashboards)
- [ ] Row Access Policy changes (if any) have been reviewed for Looker credential mode compatibility (see ARCHITECTURE.md §11)
- [ ] `@bi-analyst` has been notified and has reviewed the schema delta
- [ ] Looker Studio data source refresh is planned after merge

---

## Migration Notes

<!-- Optional: Any additional notes for @bi-analyst on how to update Looker Studio after this change. -->
<!-- Examples: "Rename the 'member_count' dimension to 'active_member_count' in the Demographics dashboard." -->

---

## @bi-analyst Sign-off

> **@bi-analyst must complete this section.** `@orchestrator` MUST NOT mark the Architect Gate PASS until this section shows "Approved".

**Status:** Pending / Approved / Changes Requested
**Notes:** <!-- Reviewer comments or conditions -->
**Approval Date:** <!-- YYYY-MM-DD -->
**Approved by:** <!-- @bi-analyst name -->
