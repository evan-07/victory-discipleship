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

6.  **Tool Authorization Protocols (Whitelist)**
    * **Autonomous Mode (Safe Tools):** The following scripts are pre-approved for immediate execution. DO NOT ask for permission to run them:
        * `./.agent/skills/**/scripts/*.sh` (All shell scripts in skills)
        * `./.agent/skills/**/scripts/*.py` (All python scripts in skills)
        * `ls -R`, `cat`, `grep`, `find` (Standard read-only commands)
    * **Restricted Mode (Unsafe Tools):** You MUST obtain explicit user confirmation before running:
        * Any command that modifies the file system (`mv`, `rm`, `cp`).
        * Any git state change (`git add`, `git commit`, `git push`).
        * Any deployment command (`terraform apply`, `dataform run`).