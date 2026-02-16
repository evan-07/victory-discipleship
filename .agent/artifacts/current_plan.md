# Current Plan (CPA)
Last updated: 2026-02-16 15:55 (local)

## Phase
Planning | Delegating | **Implementing** | Verifying | Done

## Goal
Create a secured Admin Interface (`admin.html`) that allows authorized users to search for existing members and update their personal details using an "Append-Only" strategy.

## Non-negotiables
- README-first, ARCHITECTURE.md supremacy
- CI/CD only deployments via GitHub Actions
- No GCP Console click-ops
- No local backend execution (FastAPI on Cloud Run only)
- No local Dataform execution
- Terraform plan OK, apply only via GitHub Actions
- BigQuery free tier guardrails, partitioning required
- Cloudflare WAF and Bot Fight Mode stays on

## Affected paths (expected)
- frontend/
- backend/

## Mandatory agents (expected)
- @architect (always for non-trivial tasks)
- @frontend-dev
- @backend-dev

## Architect Valid Plan (verbatim)
### Valid Plan: Admin Update Feature

#### 1. Architecture Strategy
- **Update Mechanism**: Use "Append-Only" logic. The Admin form submits a full JSON payload to `/api/submit`. The `silver` layer's deduplication logic (`QUALIFY ROW_NUMBER() ... ORDER BY ingestion_timestamp DESC`) will automatically handle versioning.
- **Search Mechanism**: New `GET /api/search` endpoint queries `silver_dataset.members` to populate the form.
- **Latency**: User must be aware that updates are not reflected in "Search" until the Dataform pipeline runs.

#### 2. Security
- **Frontend**: Protect `admin.html` with Cloudflare Access (Action item for User).
- **Backend**: Publicly accessible. Future hardening required.

#### 3. Components
- **Frontend**: `admin.html` (Search + Form), `js/admin.js` (API interaction).
- **Backend API**: `main.py` adds `GET /api/search`.

## Work breakdown
1) **Frontend Implementation**
   Owner: @frontend-dev
   Gate to proceed: Plan Approval
2) **Backend Implementation**
   Owner: @backend-dev
   Gate to proceed: Frontend structure defined
3) **Verification**
   Owner: @orchestrator
   Gate to proceed: Deployment to Dev/Preview

## Verification plan
- **Automated**: Backend unit tests for `GET /api/search`.
- **Manual**: 
    1. Search for user -> Verify data.
    2. Update user -> Verify success message.
    3. Check BigQuery `bronze` table for new row.