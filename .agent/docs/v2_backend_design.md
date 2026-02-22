# V2 Architecture Backend Design Spec
**Status:** Planning (Not Implemented)

## Overview
The backend for Phase 1 will be a stateless, serverless application built with Python 3.12 and **FastAPI**, hosted on **Google Cloud Run**. The primary purpose of the backend is to accept form submissions, validate JWT tokens, and stream data into BigQuery Bronze layer.

## Project Structure
```plaintext
backend/
├── main.py              # Entry point. FastAPI app, routes, middleware
├── requirements.txt     # Dependencies
└── Dockerfile           # Container definition
```

## Key Technologies
- **FastAPI**: Provides automatic input validation (via Pydantic) and builds OpenAPI docs automatically.
- **Firebase Admin SDK**: Validates Google Sign-In JWT tokens sent from the frontend.
- **google-cloud-bigquery**: For streaming inserts directly into `victory_bronze` datasets.
- **google-cloud-pubsub**: For triggering the near-real-time discipleship pipeline upon attendance creation.

## Auth Middleware (Phase 1)
- The backend will implement a standard FastAPI Dependency that extracts the `Authorization: Bearer <token>` header.
- This token will be verified using `firebase_admin.auth.verify_id_token`.
- The extracted `uid` (google_uid) and `email` will be attached to the request state and used for RBAC against `silver.person_roles`.

## Phase 1 API Routing
- `GET /health` : Returns 200 OK `{"status": "healthy"}`. Used by CI/CD and uptime monitoring.
- `GET /api/me`: Look up the current signed-in user against `victory_silver.persons` by `google_uid`. Returns their profile and groups led (if any).
- `POST /api/submit`: The core endpoint. Accepts the JSON payload for the VG Leader form. Writes the action to `victory_bronze.raw_form_submissions` via a streaming insert.

## Constraints & Rules
- **No Local Execution**: The backend must never be executed locally via `uvicorn`. The application will only run safely within Cloud Run.
- **No Mutations**: The API will never perform `UPDATE` clauses on the database. It will strictly perform append-only `INSERT` operations into the Bronze layer schema.
- **Secrets Management**: Setup `FIREBASE_SERVICE_ACCOUNT` through Secret Manager. Fast API will load these upon initialization.
