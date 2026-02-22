# V2 Architecture Dataform Design Spec
**Status:** Planning (Not Implemented)

## Overview
The Dataform implementation orchestrates the transformation pipeline in Google BigQuery. It extracts append-only data from the Bronze tables, applies business logic, deduplicates records, and merges them securely into the Silver tables using Slowly Changing Dimensions Type 2 (SCD2).

## Project Structure
```plaintext
data/
├── dataform.json        # Main configuration
└── definitions/
    ├── 1_bronze/        # Declarations of source tables created by Cloud Run
    └── 2_silver/        # Transformation logic (.sqlx)
```

## Phase 1 Table Targets

### Bronze Declarations
- `victory_bronze.raw_form_submissions`
- `victory_bronze.raw_event_actions`
- `victory_bronze.raw_bulk_imports`

### Silver Aggregations (SCD2)
- `victory_silver.persons`
- `victory_silver.person_contacts`
- `victory_silver.person_occupations`
- `victory_silver.person_roles`
- `victory_silver.victory_groups`
- `victory_silver.victory_group_members`

## SCD2 Logic Implementation
For tables such as `silver.persons` that track historical progression (e.g., as a person progresses through the Journey Stages), Dataform's `type: incremental` configuration will be leveraged heavily.
Each `.sqlx` file will define:
- `uniqueKey`: E.g., `google_uid` for a person.
- `updateStrategy`: How we expire old records by updating `valid_to` and setting `is_current = FALSE`.

## Pipeline Triggers
- **Routine Updates**: The primary execution mechanism for standard pipeline components will be handled by a Cloud Scheduler cron job (every 15 mins).
- **Automated Deployments**: Code changes to `.sqlx` files merged into `main` will trigger the GitHub Action to compile and execute Dataform definitions to update the schemas in BigQuery immediately.

## Data Governance & Error Checking
- **Assertions**: `assert` blocks will be heavily utilized in Dataform to prevent malformed data from progressing to Silver. We will assert `person_id IS NOT NULL` and enforce regex patterns on emails. 
- **Idempotency**: All queries will be fully idempotent; running the pipeline multiple times without new Bronze data will result in 0 changes to Silver.
