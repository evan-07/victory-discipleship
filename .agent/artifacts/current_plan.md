# Current Plan (CPA)

| Field | Content |
|---|---|
| Phase | Done |
| Goal | Plan and implement updates in `.agent/workflows` and `.github/workflows` to align with `ARCHITECTURE.md` and the usage of the new branch `feature/v2-architecture` as the development branch. |
| Non-negotiables | `ARCHITECTURE.md` is supreme. Workflows must be updated to use the new development branch, `feature/v2-architecture`. Wait for Architect Valid Plan. |
| Affected Paths | `.github/workflows/*.yaml`, `.agent/workflows/*.md` |
| Mandatory Agents | `@architect`, `@infra-ops` |
| Documentation Impact | Multiple `.agent/workflows/` files updated to direct users to pull from and PR to `feature/v2-architecture`. |
| Architect Valid Plan | **Valid Plan:** User approved the implementation. |
| Steps+Owners | 1. Identify `main` branch usages in workflows (`@orchestrator`) [DONE], 2. Draft Implementation Plan (`@orchestrator`) [DONE], 3. Architect Review (`@architect`) [DONE], 4. Implementation (`@infra-ops`, `@orchestrator`) [DONE]. |
| Verification Plan | Verify all references to `main` branch have been safely replaced without affecting `main.py` or `main.tf`. [VERIFIED] |