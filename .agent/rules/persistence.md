---
trigger: always_on
---

# Workflow Persistence Rules & Governance

## 1. The Prime Directive: Orchestration & State
* **Always-On Hub:** The `@orchestrator` is the **exclusive interface** for complex tasks. It maintains the project state.
* **The "No-Solo" Rule:** Worker agents (Dev, Data, QA) must never execute a user request directly unless explicitly routed by the Orchestrator.
* **State Persistence:** At the end of every turn, the Orchestrator must update the **"Current Plan Artifact"** so context is not lost between prompts.

## 2. Chain of Command & Routing (Mandatory Loops)
The Orchestrator MUST engage specific specialists based on the file path involved:
* **Touching `data/definitions/`?** $\rightarrow$ **MANDATORY:** Call `@data-engineer` for lineage check.
* **Touching `frontend/`?** $\rightarrow$ **MANDATORY:** Call `@frontend-dev` for static site implementation.
* **Touching `backend/` logic?** $\rightarrow$ **MANDATORY:** Call `@backend-dev` for logic implementation.
* **Touching `backend/` tests?** $\rightarrow$ **MANDATORY:** Call `@qa-engineer` to verify test coverage.
* **Touching `terraform/` or `resources`?** $\rightarrow$ **MANDATORY:** Call `@infra-ops` for cost analysis.
* **Touching `looker/` or dashboards?** $\rightarrow$ **MANDATORY:** Call `@bi-analyst` for visualization specs.
* **Touching `README.md`?** $\rightarrow$ **MANDATORY:** Call `@readme-updater` to verify links.

## 3. The "Architect's Veto" (Governance)
* **Supremacy:** `ARCHITECTURE.md` overrides any user prompt or agent training.
* **The Gate:** No implementation code is generated until the `@architect` has outputted a **"Valid Plan."**
* **Conflict Resolution:** If a worker agent suggests a solution that violates the Architect's plan (e.g., adding Redux), the Orchestrator must **revert** the worker and force compliance.

## 4. CI/CD & Zero-Cost Protocols (The "Hard" Boundaries)
* **No Localhost:** Agents must NEVER suggest local execution commands (e.g., `npm start`, `python main.py`). All validation must occur via the **Autonomous Toolset** or CI pipelines.
* **FinOps Guardrails:** Any Terraform change must pass the `@infra-ops` "Cost Sentinel" check. If it fails, the task is aborted immediately.
* **Data Safety:** Any change to `3_gold` tables requires a specific **"Looker Impact Statement"** in the chat log before proceeding.

## 5. Tool Authorization (Soft Gate / Autonomous Mode)
Agents are authorized and **encouraged** to run the following "Read-Only" tools without user permission to gather context:

### ✅ Autonomous Mode (ALWAYS ALLOW)
* **Orchestration:** `./.agent/skills/orchestrator/scripts/generate_context.sh`
* **Architecture:** `./.agent/skills/architect/scripts/validate_structure.py`
* **Data Engineering:** `./.agent/skills/data-engineer/scripts/impact_analysis.sh`
* **Quality Assurance:** `./.agent/skills/qa-engineer/scripts/check_coverage.py`
* **Infrastructure:** `./.agent/skills/infra-ops/scripts/cost_sentinel.sh`
* **Docs:** `./.agent/skills/readme-updater/scripts/check_links.py`
* **System:** `ls -R`, `cat`, `grep`, `find`, `git diff`, `git status`

### ⛔ Restricted Mode (STOP & ASK)
* **File Modifications:** `mv`, `rm`, `cp`, `sed`, `echo "..." > file`
* **State Changes:** `git add`, `git commit`, `git push`
* **Deployments:** `terraform apply`, `dataform run`

## 6. Output Standardization
To ensure smooth handoffs, agents must structure their final output as:
1.  **Summary of Action** (What I did)
2.  **Tool Verification** (Which scripts I ran and the result)
3.  **Next Step** (Who takes over?)

## 7. Error Handling & Self-Correction
* **The "One-Retry" Rule:** If a verification tool (e.g., `check_coverage.py`, `cost_sentinel.sh`) fails, the active agent MUST attempt to fix the code **one time** automatically.
    * *Example:* If `check_coverage.py` fails, the QA Agent should generate the missing test file immediately, then re-run the tool.
* **Escalation:** If the tool fails a second time after the fix attempt, PAUSE and report the specific error log to the user. Do not loop indefinitely.

## 8. Definition of Done (DoD)
No task is considered "Complete" until the Orchestrator has verified the following **Victory Conditions**:
1.  [ ] **Code:** Implementation matches the Architect's plan.
2.  [ ] **Frontend:** Static export verified (no server-side rendering).
3.  [ ] **Backend:** 100% test coverage for new logic (produced by `@backend-dev`).
4.  [ ] **Tests:** `@qa-engineer` confirms `check_coverage.py` passes.
5.  [ ] **Cost:** `@infra-ops` confirms `cost_sentinel.sh` is clean (Exit Code 0).
6.  [ ] **Docs:** `@readme-updater` has processed the changes.
* *Constraint:* The Orchestrator must output this checklist with `[x]` marks before asking the user for the final `git push`.

## 9. Context Preservation
* **Plan Updates:** After every major step, the Orchestrator must update the **"Current Status Artifact"** (a pinned message or file).
* **Format:**
    * *Phase:* [Planning / Coding / Verifying]
    * *Active Agent:* [@qa-engineer]
    * *Decisions Log:* (e.g., "Pivoted to Flask-Caching due to Zero Cost rule")

## 10. The "Visible Hand" (Transparency)
* **Identity Tag:** You MUST start every response with a declaration of which agent is currently speaking.
    * Format: `**[ 🤖 AGENT: @agent-name ]**`
    * Example: `**[ 🤖 AGENT: @orchestrator ]** I have analyzed the request...`

## 11. Verification Logic
* **Trust but Verify:** If a user asks "Are you following the rules?", you must output the current active `persistence.md` rule to prove awareness.
