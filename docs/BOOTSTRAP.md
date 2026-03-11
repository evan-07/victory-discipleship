# System Bootstrap — First Admin User

← Part of [ARCHITECTURE.md](../ARCHITECTURE.md) | See also: [API.md](API.md) · [SCHEMA.md](SCHEMA.md)

---

This procedure is run **once** after the initial Terraform apply, by a developer with GCP project IAM (`bigquery.dataEditor` or higher) access. It seeds the founding admin record directly in BigQuery.

There is no product UI for this step — it is intentionally a developer-only action. The system cannot assign admin roles through the app until at least one admin exists.

---

## Prerequisites

- [ ] Terraform `apply` completed successfully
- [ ] BigQuery datasets `victory_silver` and `victory_bronze` exist
- [ ] Tables `victory_silver.persons` and `victory_silver.person_roles` exist
- [ ] The founding admin has signed in to Firebase **at least once** via the app — this creates their Firebase Auth account and generates a `google_uid`
- [ ] You have retrieved the founding admin's `google_uid` from the Firebase Console (`Authentication → Users → copy UID`)

---

## Step 1 — Create the Person Record

Run in **BigQuery Console** or via `bq` CLI. Replace all placeholder values.

```sql
INSERT INTO `{GCP_PROJECT_ID}.victory_silver.persons`
  (
    person_id, google_uid,
    first_name, last_name, full_name,
    journey_stage, review_status, source,
    is_current, valid_from,
    one2one_completed, duplicate_flag, profile_completeness_pct
  )
VALUES
  (
    GENERATE_UUID(),
    '<FIREBASE_UID>',          -- from Firebase Console → Authentication → Users
    '<FIRST_NAME>',
    '<LAST_NAME>',
    '<FULL_NAME>',             -- TRIM(CONCAT_WS(' ', first_name, [middle_name], last_name))
    'leader',
    'approved',
    'admin_created',
    TRUE,
    CURRENT_TIMESTAMP(),
    FALSE,
    FALSE,
    0                          -- Dataform will recalculate on next run
  );
```

---

## Step 2 — Assign the Admin Role

Run immediately after Step 1. Uses a subquery to resolve `person_id` from the `google_uid` inserted above.

```sql
INSERT INTO `{GCP_PROJECT_ID}.victory_silver.person_roles`
  (role_id, person_id, role, assigned_by, assigned_at, is_active)
SELECT
  GENERATE_UUID(),
  person_id,
  'admin',
  person_id,        -- self-assigned on bootstrap; no pre-existing admin to reference
  CURRENT_TIMESTAMP(),
  TRUE
FROM `{GCP_PROJECT_ID}.victory_silver.persons`
WHERE google_uid = '<FIREBASE_UID>'
  AND is_current = TRUE;
```

---

## Verification

After running both steps, verify the records were created correctly:

```sql
-- Confirm person record
SELECT person_id, google_uid, full_name, journey_stage, review_status, is_current
FROM `{GCP_PROJECT_ID}.victory_silver.persons`
WHERE google_uid = '<FIREBASE_UID>' AND is_current = TRUE;
-- Expected: 1 row, journey_stage = 'leader', review_status = 'approved'

-- Confirm role record
SELECT r.role_id, r.role, r.is_active, p.full_name
FROM `{GCP_PROJECT_ID}.victory_silver.person_roles` r
JOIN `{GCP_PROJECT_ID}.victory_silver.persons` p
  ON r.person_id = p.person_id AND p.is_current = TRUE
WHERE r.role = 'admin' AND r.is_active = TRUE;
-- Expected: 1 row, role = 'admin', is_active = TRUE
```

The founding admin can now sign in via Google and access `/admin.html`.

---

## Additional Admins

Once the first admin is active, additional admins can be assigned via the app:
1. The target person signs in and their profile appears in the `/admin.html` review queue.
2. The founding admin approves the record.
3. The founding admin navigates to the person's record → Roles section → assigns the `admin` role.

No further direct BigQuery writes are required after the bootstrap.

---

## Notes

- This bootstrap INSERT is performed outside Cloud Run and is therefore **not logged** in `victory_silver.data_change_log`. This is acceptable as a one-time setup action.
- Document the bootstrap date and the founding admin's `person_id` in your deployment runbook for audit purposes.
- If Step 2 is accidentally run twice, the second INSERT will create a duplicate role record. Deactivate the duplicate: `UPDATE victory_silver.person_roles SET is_active = FALSE WHERE role_id = '<duplicate_role_id>'`.

---

*Owner: @infra-ops. Created: 2026-03-12. Bootstrap procedure for Phase 1 initial deployment.*
