# CPA: Centralizing Agent Governance

Phase: Planning
Goal: Implement AGENTS.md to centralize agent roles and routing.
Non-negotiables: Must not violate ARCHITECTURE.md supremary; must use relative file links.
Affected Paths:
- /Users/erivanbuenaventura/AntiGravity/victory-discipleship/AGENTS.md
- /Users/erivanbuenaventura/AntiGravity/victory-discipleship/README.md
- /Users/erivanbuenaventura/AntiGravity/victory-discipleship/ARCHITECTUREv4.1.md

Mandatory Agents: @orchestrator, @architect, @readme-updater

Documentation Impact: Updates README.md and ARCHITECTURE.md references.

Architect Valid Plan:
1. Create `AGENTS.md` containing the Agent Roster and Routing Matrix.
2. Update `README.md` Section 3 to link to `AGENTS.md`.
3. Update `ARCHITECTUREv4.1.md` Section 15 to reference `AGENTS.md`.
4. Run `check_links.py` to verify documentation integrity.

Steps+Owners:
1. Research AGENTS.md and draft content (@orchestrator)
2. Create AGENTS.md (@orchestrator)
3. Update README.md (@readme-updater)
4. Update ARCHITECTURE.md (@architect)
5. Verify links (@readme-updater)

Verification plan:
- check_links.py
- validate_structure.py