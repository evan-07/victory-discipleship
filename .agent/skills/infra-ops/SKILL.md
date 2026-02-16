---
name: infra-ops
description: Manages Terraform and enforces Free Tier constraints.
---

# Infrastructure & FinOps Specialist

## Goal
Maintain Infrastructure-as-Code (IaC) while strictly adhering to the "Zero Cost" policy.

## Tools (Soft Gate: ALLOWED)
* **Cost Sentinel:** `bash .agent/skills/infra-ops/scripts/cost_sentinel.sh`
    * *Action:* Scans `.tf` files for banned keywords (e.g., `n1-standard-1`, `Cloud NAT`, `Load Balancer`). Use `--help` for details.
* **Format Check:** `terraform fmt -check -recursive` (Read-only)

## Workflow
1.  **Request:** User wants "Automatic backups."
2.  **Plan:**
    * Design the Terraform resource (e.g., `google_storage_bucket`).
    * **Constraint:** Must set `storage_class = "STANDARD"` and `location = "US"` (cheapest).
3.  **Validate:**
    * Run `cost_sentinel.sh`.
    * If it detects a non-free resource, REJECT the plan.