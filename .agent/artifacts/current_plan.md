# Current Plan (CPA)
Last updated: 2026-02-16T19:40:00+08:00

## Phase
**Planning** | Delegating | Implementing | Verifying | Done

## Goal
Remove all existing Gold and Silver analytical views/tables (15 files total) and rebuild from scratch using `silver_dataset.members` as foundation. Create simplified data model for basic demographics Looker dashboards.

## Non-negotiables
- README.md read first (completed)
- ARCHITECTURE.md supremacy (completed)
- Medallion Architecture (Bronze → Silver → Gold)
- No Click-Ops (Terraform only for GCP changes)
- No local Dataform execution (GitHub Actions only)
- BigQuery partitioning required (_PARTITIONDATE)
- Looker Impact Statement required (Section 7, persistence.md)
- Cost-efficient queries (avoid full table scans)

## Affected Paths
**Deletions** (15 files):
- `data/definitions/2_silver/view_*.sqlx` (8 files: demographics, leadership_summary, marketplace_sector, campus_sector, discipleship_journey, growth_metrics, ministry_involvement, vg_involvement)
- `data/definitions/3_gold/*.sqlx` (7 files: dim_members, summary, view_stats, rept_*)

**New Files**:
- `data/definitions/3_gold/dim_members.sqlx` (simplified schema)

**Documentation**:
- `FUTURE_IMPROVEMENTS.md` (document removed features)

## Mandatory Agents Triggered
- `@architect` (REQUIRED for Valid Plan approval)
- `@data-engineer` (REQUIRED for data/definitions/** changes + Looker Impact Statement)
- `@bi-analyst` (REQUIRED for Looker dashboard specs)
- `@readme-updater` (conditional: only if ARCHITECTURE.md/README.md need updates)

## Documentation Impact
**ARCHITECTURE.md**: No changes required (no new API endpoints, frontend pages, or GCP resources)

**README.md**: No changes required (no workflow changes)

**FUTURE_IMPROVEMENTS.md**: Should document removed features for potential re-addition

## Architect Valid Plan
**APPROVED** - 2026-02-16T19:42:30+08:00

```
VALID PLAN APPROVED - Data Pipeline Restructure

Scope:
- DELETE: 8 Silver analytical views (2_silver/view_*.sqlx)
- DELETE: 7 Gold tables (3_gold/*.sqlx)
- CREATE: New simplified dim_members.sqlx with demographics focus
- PLAN: 5 Looker dashboard specifications

Architectural Compliance:
✅ Medallion Architecture maintained
✅ No local execution (GitHub Actions only)
✅ BigQuery partitioning required (_PARTITIONDATE)
✅ Gold layer only for Looker (no Bronze/Silver exposure)
✅ No infrastructure changes (no terraform, no cost impact)
✅ Looker Impact Statement included (BREAKING change documented)

This plan adheres to ARCHITECTURE.md Section 2 (Governance) and Section 3 (Technology Stack).
```

## Work Breakdown (Post-Approval)

### Step 1: Architect Review
**Owner**: @architect
- Review implementation_plan.md
- Run `validate_structure.py` if needed
- Issue "Valid Plan" or request revisions

### Step 2: Data Engineer - Looker Impact Statement
**Owner**: @data-engineer
- Confirm Looker Impact Statement in implementation_plan.md is acceptable
- Verify removal of 15 files won't break undocumented dependencies
- Run `impact_analysis.sh` on removed columns

### Step 3: BI Analyst - Looker Specs
**Owner**: @bi-analyst
- Generate Looker configuration specs for 5 dashboards:
  1. Demographics by Gender
  2. Demographics by Age Group
  3. Demographics by Marital Status
  4. VG Leaders count & people led
  5. Occupation breakdown
- Use `generate_looker_spec.py` with new `dim_members` schema

### Step 4: Implementation (Post-Approval)
**Owner**: @data-engineer
- Delete 8 Silver views
- Delete 7 Gold tables
- Create new `dim_members.sqlx` with simplified schema
- Run `schema_lint.py` verification
- Commit to branch, create PR

### Step 5: Verification
**Owners**: @orchestrator, @data-engineer
- Verify Dataform compiles via GitHub Actions
- Verify BigQuery tables created successfully
- User creates Looker dashboards using @bi-analyst specs

## Verification Plan
**Pre-Implementation**:
- @architect "Valid Plan" approval
- @data-engineer Looker Impact Statement accepted
- User approval of BREAKING change

**Post-Implementation**:
- Dataform compilation passes (GitHub Actions)
- `schema_lint.py` PASS
- `impact_analysis.sh` confirms no unexpected dependencies
- User successfully creates Looker dashboards