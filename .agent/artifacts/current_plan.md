# Current Plan (CPA)

**Phase:** Planning

**Goal:** Fix Dataform pipeline error where `silver_dataset.stg_members` table cannot be replaced due to partitioning spec mismatch.

**Non-negotiables:**
- Must follow GitOps principles (no manual GCP Console changes if possible)
- Must maintain data integrity (regenerate from Bronze layer)
- Must comply with ARCHITECTURE.md partitioning requirements

**Affected Paths:**
- `data/definitions/2_silver/stg_members.sqlx` (potentially)
- BigQuery table: `silver_dataset.stg_members`

**Mandatory Agents:**
- @data-engineer (primary)
- @architect (review Click-Ops exception if needed)

**Documentation Impact:**
- None (one-time fix)

**Architect Valid Plan:**
*(Pending architect review)*

**Steps + Owners:**
1. @orchestrator: Analyze error and create implementation plan ✅
2. @data-engineer: Review approaches and recommend solution
3. @orchestrator: Get user approval on approach
4. @data-engineer: Implement chosen solution
5. @orchestrator: Verify fix in GitHub Actions

**Verification Plan:**
- Monitor GitHub Actions Dataform workflow
- Query BigQuery INFORMATION_SCHEMA to confirm partitioning
- Verify data regeneration in Silver and Gold layers