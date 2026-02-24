# Security Architecture

← Part of [ARCHITECTURE.md](../ARCHITECTURE.md) | See also: [API.md](API.md) · [DEVOPS.md](DEVOPS.md)

---

## Security Architecture

Seven-layer defense-in-depth — no single point of failure.

### Access Control Layers

```plaintext
LAYER 1: Network       Cloudflare WAF (Bot Fight Mode + Geo-blocking)
LAYER 2: Auth          Firebase Auth (Google Sign-In only — no passwords)
                              │
                    (Cloud Run receives JWT)
                              │
                              ▼
LAYER 3: API Role      FastAPI Role-Based Access (RBAC)
                       Checks victory_silver.person_roles table
                              │
                    (API requests BigQuery data)
                              │
                              ▼
LAYER 4: Database      BigQuery Row-Level Security
                       Filtered by SESSION_USER() email
```

| Layer | Technology | What It Protects Against | Configuration |
| :--- | :--- | :--- | :--- |
| 1 — Edge | Cloudflare WAF + DDoS | SQL injection, XSS, brute force, DDoS attacks, bots | Free managed ruleset + OWASP Core Rule Set enabled |
| 2 — Transport | HTTPS / TLS 1.3 (Cloudflare) | Man-in-the-middle, data interception, certificate spoofing | Full (strict) SSL mode, HSTS with 1-year max-age |
| 3 — Authentication | Firebase Auth (Google OAuth 2.0) | Unauthorized access, credential stuffing, password attacks | Google Sign-In only — no passwords to breach |
| 4 — Authorization | Cloud Run role middleware (FastAPI) | Privilege escalation, unauthorized API calls | JWT claims verified + role looked up in victory_silver.person_roles on every request |
| 5 — Data | BigQuery Row Access Policies | Data leakage between personas | Leader can only query their own rows — enforced at DB engine, not app layer |
| 6 — Secrets | Google Secret Manager | Credential exposure in code, logs, or env vars | Secrets accessed at runtime only via IAM-scoped service account |
| 7 — Code | SonarCloud SAST + pip-audit | Vulnerable dependencies, insecure code patterns | Blocks merges with OWASP-classified vulnerabilities |

### BigQuery Row Access Policy — SQL Reference

Row access policies are defined in Terraform using `google_bigquery_row_access_policy` resources. The policies use `SESSION_USER()` to match the authenticated caller's email at query time.

> **Critical Looker Studio constraint:** Looker Studio connects to BigQuery using the **Looker Studio service account** (`looker-studio-sa`), NOT the individual viewer's Google identity. This means `SESSION_USER()` in a standard row access policy resolves to the service account email, NOT the viewer's email — breaking per-leader row filtering.
>
> **Approved solution for `vw_leader_dashboard`:** Configure the Looker Studio data source with **"Viewer's credentials"** mode (Zero Trust → Data Credentials → Viewer's credentials). In this mode, BigQuery receives queries under the viewer's own Google account identity, so `SESSION_USER()` resolves correctly. Each VG Leader MUST have `bigquery.filteredDataViewer` IAM role on the `victory_gold` dataset.
>
> **For executive/admin views** that do NOT need per-viewer filtering: use "Owner's credentials" (service account). Standard IAM dataset-level access applies.

#### Policy: VG Leader Dashboard (leader sees only their own rows)

```sql
-- Applied to: victory_gold.vw_leader_dashboard
-- Requires: Looker Studio data source configured with "Viewer's credentials"
CREATE OR REPLACE ROW ACCESS POLICY leader_row_filter
ON `victory_gold.vw_leader_dashboard`
GRANT TO ("domain:victorychurch.ph")
FILTER USING (leader_email = SESSION_USER());
```

#### Policy: Sensitive Events (admin-only for is_sensitive = TRUE rows)

```sql
-- Admins see all rows (no filter)
CREATE OR REPLACE ROW ACCESS POLICY admin_all_rows
ON `victory_gold.vw_pastoral_events`
GRANT TO ("group:admins@victorychurch.ph")
FILTER USING (TRUE);

-- Non-admin viewers see only non-sensitive rows
CREATE OR REPLACE ROW ACCESS POLICY non_sensitive_only
ON `victory_gold.vw_pastoral_events`
GRANT TO ("domain:victorychurch.ph")
FILTER USING (is_sensitive = FALSE);
```

**Terraform resource pattern:**
```hcl
resource "google_bigquery_row_access_policy" "leader_filter" {
  project      = var.project_id
  dataset_id   = "victory_gold"
  table_id     = "vw_leader_dashboard"
  policy_id    = "leader_row_filter"
  filter_predicate = "leader_email = SESSION_USER()"
  grantees     = ["domain:victorychurch.ph"]
}
```

> **IAM Reconciliation — Automated (periodic):** A scheduled reconciliation script runs hourly (or daily) to sync `bigquery.filteredDataViewer` IAM bindings with the current set of active VG Leaders in `victory_silver.person_roles`. The script queries `victory_silver.person_roles WHERE role = 'vg_leader' AND is_active = TRUE`, retrieves each leader's `email` from `victory_silver.persons`, and applies the `google_bigquery_dataset_iam_member` binding for `victory_gold` via the GCP IAM API. Leaders whose `is_active` is set to `FALSE` are removed from the binding on the next reconciliation run. This eliminates the manual Terraform-per-leader action previously required. The reconciliation script is Terraform-managed as a Cloud Scheduler job + Cloud Function.

### Cloudflare Access (Admin Gate)

The `/admin` and `/events` pages are additionally protected by Cloudflare Access (free for up to 50 users). This adds a zero-trust authentication layer at the CDN edge — before the page even loads. Only email addresses in the approved list can access these paths. A valid Firebase Auth token is then also required to make any API calls.

**Email whitelist management procedure:**

The Cloudflare Access policy for `/admin` and `/events` is managed via the Cloudflare dashboard (Zero Trust → Access → Applications):
1. Admin adds a new staff member's Google email to the Access policy "Allow" rule.
2. Admin removes departed staff members' emails from the "Allow" rule.

> **Click-Ops Exception (documented):** Cloudflare Access email whitelist management is the **only** permitted manual Cloudflare dashboard action. All other Cloudflare configuration (DNS, WAF rules, Pages project) remains Terraform-managed. Capacity: free tier supports up to 50 unique users.

### Principle of Least Privilege — IAM Roles

| Service Account | BigQuery Role | Other Roles |
| :--- | :--- | :--- |
| Cloud Run (backend) | `bigquery.dataEditor` on `silver` only | `secretmanager.secretAccessor`, `pubsub.publisher` |
| Dataform | `bigquery.dataEditor` on `silver` + `gold`; `bigquery.dataViewer` on `bronze` | None additional |
| Cloud Functions (`dataform-attendance-trigger`) | None (calls Dataform API, not BigQuery directly) | `dataform.editor` on Dataform repository; `pubsub.subscriber` |
| Looker Studio | `bigquery.dataViewer` on `gold` dataset only | None additional |
| GitHub Actions (deploy) | None (Terraform manages BigQuery) | `run.admin`, `artifactregistry.writer`, `iam.serviceAccountUser` |
| GitHub Actions (Terraform) | `bigquery.admin` (for schema management only) | `resourcemanager.projectIamAdmin` (scoped) |

### Data Sovereignty

All data resides strictly within GCP Philippines/Taiwan regions. No member data is processed or stored by external SaaS providers. Cloudflare handles only edge traffic — no member PII passes through it.

---

*Owner: @architect. Last updated: 2026-02-24.*
