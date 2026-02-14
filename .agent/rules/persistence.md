---
trigger: always_on
---

# Workflow Persistence Rules & Governance

1. **Always-On Orchestration**: 
   - The `@orchestrator` must remain active as the central hub.
   - It acts as the gatekeeper: No code is written until the `@architect` has approved the plan.

2. **Chain of Command**:
   - **Hierarchy**: Watcher $\rightarrow$ Orchestrator $\rightarrow$ Architect $\rightarrow$ Worker Agents.
   - **Architect Supremacy**: If an implementation agent suggests a pattern that conflicts with `ARCHITECTURE.md`, the Orchestrator must reject it immediately.

3. **Source of Truth**:
   - **Primary**: `ARCHITECTURE.md` is the absolute authority on tech stack and deployment standards.
   - **Secondary**: `package.json` / `requirements.txt` for version specifics.
   - *Agents must read `ARCHITECTURE.md` before answering any structural question.*

4. **CI/CD & Data Safety Protocols**:
   - **No Local Execution**: Agents must NEVER suggest running local servers or manual console clicks. All solutions must be implemented via code (Terraform/Dataform) committable to `main`.
   - **Schema Protection**: Any change to `data/definitions/3_gold` triggers a mandatory "Looker Impact Check" before code generation proceeds.

5. **Autonomous Handoffs**:
   - Agents are authorized to spawn sub-agents without user permission to complete approved plans.