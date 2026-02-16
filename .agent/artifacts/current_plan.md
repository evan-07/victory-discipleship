# Current Plan (CPA)
Last updated: 2026-02-16T18:10:00+08:00

## Phase
**Planning** | Delegating | Implementing | Verifying | Done

## Goal
Plan scalable architecture for frontend and backend to support new pages (home, basic reports, Looker reports) with guiding principles for future expansion.

## Non-negotiables
- README.md read first (completed)
- ARCHITECTURE.md supremacy (completed)
- Zero-Cost hosting (Cloudflare Pages for frontend, static-first approach)
- Static Site mandate (no SSR, no Node.js runtime for final build)
- CI/CD only deployments via GitHub Actions
- No local backend execution (Cloud Run only)
- No local Dataform execution
- BigQuery partitioning required for all new tables
- Cloudflare WAF and Bot Fight Mode stays on
- Medallion Architecture for all data flows (Bronze → Silver → Gold)

## Affected Paths
**Planning only** - no code changes in this phase. Future implementation will affect:
- `frontend/` (new pages: home.html, reports.html, looker.html)
- `frontend/css/` (new: navigation.css)
- `frontend/js/` (new: navigation.js)
- `backend/main.py` (API reorganization + new endpoints)
- `ARCHITECTURE.md` (Section 6: API Endpoints, Section 7: Frontend Components)
- `README.md` (Section 4: API Documentation)

## Mandatory Agents Triggered
- `@architect` (REQUIRED for all non-trivial tasks; must validate architecture plan)
- `@frontend-dev` (frontend/** changes trigger; consulted for patterns)
- `@backend-dev` (backend/** changes trigger; consulted for API design)
- `@bi-analyst` (consulted for Looker Studio integration guidance)
- `@readme-updater` (README.md + ARCHITECTURE.md updates required)

## Documentation Impact
**ARCHITECTURE.md Changes Required**:
- Section 6 (API Endpoints & Contracts): Add new REST endpoints table
- Section 7 (Frontend Components): Add new pages (home.html, reports.html, looker.html, events.html)
- Section 5 (System Design & Data Flow): Update Mermaid diagram to include Events flow

**README.md Changes Required**:
- Section 4 (API Documentation): Update endpoints table to match ARCHITECTURE.md

## Architect Valid Plan
**PENDING** - Awaiting @architect review and "Valid Plan" approval

## Work Breakdown (Post-Approval)

### Phase 1: Core Infrastructure
**Owner**: @frontend-dev
- Create navigation component (navigation.css, navigation.js)
- Update index.html and admin.html to use shared navigation

### Phase 2: Home & Reports
**Owners**: @frontend-dev, @backend-dev, @data-engineer
- Implement home.html (landing page)
- Implement /api/reports/* endpoints (backend)
- Implement reports.html (frontend)
- Ensure reports query Gold layer only (dim_members, summary, view_stats)

### Phase 3: Looker Integration
**Owners**: @frontend-dev, @bi-analyst
- Consult @bi-analyst for Looker Studio dashboard URLs
- Implement looker.html with iFrame embeds

### Phase 4: Events Management
**Owners**: @frontend-dev, @backend-dev, @data-engineer
- Implement Bronze/Silver/Gold tables for events (data layer)
- Implement /api/events/* endpoints (backend)
- Implement events.html and events/register.html (frontend)

### Phase 5: Testing & Documentation
**Owners**: @qa-engineer, @readme-updater
- Write backend tests for new endpoints
- Write frontend Playwright tests
- Update ARCHITECTURE.md and README.md
- Run check_links.py to verify documentation

## Verification Plan
**Architectural Validation**:
- Run `validate_structure.py` to ensure no forbidden imports
- User review of implementation plan (open questions about access control, events data model)
- @architect approval ("Valid Plan" issued)

**Post-Implementation Verification** (future):
- Backend tests pass (`check_coverage.py`)
- Cost sentinel passes (`cost_sentinel.sh`) - no new resources needed
- Documentation links valid (`check_links.py`)
- Frontend static export verified