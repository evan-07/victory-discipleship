**Phase:** Planning
**Goal:** Modularize `docs/UX_FLOWS_PHASE1.md` into logical chunks (`_REGISTRATION.md`, `_ADMIN_EVENTS.md`, `_ADMIN_PERSONS.md`) and update standard documentation.
**Non-negotiables:** Ensure documentation continuity. All files must maintain valid cross-links.
**Affected Paths:** `docs/UX_FLOWS_PHASE1*.md`, `ARCHITECTURE.md`
**Mandatory Agents:** @architect, @readme-updater
**Documentation Impact:** `ARCHITECTURE.md` (Document Map), `docs/UX_FLOWS_PHASE1.md`
**Architect Valid Plan:** 
1. Create `docs/UX_FLOWS_PHASE1_REGISTRATION.md` extracting Slices 1.02-1.04 logic (Public routing).
2. Create `docs/UX_FLOWS_PHASE1_ADMIN_EVENTS.md` extracting Slices 1.05-1.06 (Event management).
3. Create `docs/UX_FLOWS_PHASE1_ADMIN_PERSONS.md` extracting Slices 1.07-1.08 (Review queue and persons).
4. Prune `docs/UX_FLOWS_PHASE1.md` to serve as a high-level index.
5. Update `ARCHITECTURE.md` Document Map with the new files.
**Steps+Owners:**
1. @architect: Request Plan Validation (Current)
2. @architect: Perform the content extraction and file creation.
3. @readme-updater: Update `ARCHITECTURE.md` to reflect new files.
4. @architect: Run `check_links.py` for verification.
**Verification plan:** Run `.agent/scripts/check_links.py` and manually verify rendering of the resulting index and sub-docs.
