# Victory Discipleship Member Management System

> [!IMPORTANT]
> **AI Agent Instructions**: This README is the **single source of truth** for this repository. When analyzing the codebase, troubleshooting, or planning changes, **ALWAYS** check this document first to understand the directory structure, architectural patterns, and deployment workflows.

## 1. Project Overview

The **Victory Discipleship Member Management System** is a full-stack application designed to manage church member data. It ingests data from a public-facing website, processes it through a data warehouse pipeline, and creates actionable insights.

### Technology Stack

*   **Frontend**: Vanilla HTML/CSS/JavaScript. Lightweight, semantic, and fast. Hosted on **Cloudflare Pages**.
*   **Backend**: Python (Flask/FastAPI) running in a Docker container. Hosted on **Google Cloud Run**.
*   **Data Warehouse**: Google BigQuery.
*   **Data Pipeline**: **Dataform** (using SQLX) following the **Medallion Architecture** (Bronze $\rightarrow$ Silver $\rightarrow$ Gold).
*   **Infrastructure**: **Terraform** for Infrastructure-as-Code (IaC) on Google Cloud Platform (GCP).
*   **CI/CD**: GitHub Actions with **Workload Identity Federation (WIF)** for secure authentication.

---

## 2. Repository Map & Directory Structure

This repository is organized by architectural layer.

```mermaid
graph TD;
    root[/] --> backend[backend/];
    root --> frontend[frontend/];
    root --> data[data/];
    root --> terraform[terraform/];
    root --> workflows[.github/workflows/];

    backend --> py[main.py];
    backend --> docker[Dockerfile];
    
    frontend --> html[index.html];
    frontend --> css[css/];

    data --> bronze[definitions/1_bronze/];
    data --> silver[definitions/2_silver/];
    data --> gold[definitions/3_gold/];

    terraform --> main_tf[main.tf];
```

### 📂 Directory Descriptions

| Directory | Description | Key Tech | Hosting/Target |
| :--- | :--- | :--- | :--- |
| **`backend/`** | Contains the API logic for receiving form submissions and inserting raw data into BigQuery. | Python, Flask, Docker | Google Cloud Run |
| **`frontend/`** | The public-facing user interface. Standard web forms for data entry. | HTML5, CSS3, JS | Cloudflare Pages |
| **`data/`** | The ELT pipeline definitions. Transforms raw JSON into structured tables. | Dataform, SQLX | Google BigQuery |
| **`terraform/`** | Infrastructure definitions. Manages IAM roles, Service Accounts, and WIF. | Terraform | Google Cloud Platform |
| **`.github/workflows/`** | CI/CD pipelines for testing and deploying each component. | YAML | GitHub Actions |

---

## 3. Architecture & Data Flow

### Medallion Architecture
We strictly follow the **Medallion Architecture** pattern for our data pipeline:

1.  **Bronze Layer (Raw)**:
    *   **Source**: `backend/main.py` inserts raw JSON payloads here.
    *   **Schema**: `definitions/1_bronze/`. Contains `ingestion_timestamp`, `payload` (JSON), and `metadata`.
    *   **Goal**: Immutable, append-only store of all incoming data.
2.  **Silver Layer (Cleansed)**:
    *   **Dataform**: `definitions/2_silver/`.
    *   **Goal**: Parsed JSON, deduplicated records, type casting, and data quality assertions.
3.  **Gold Layer (Curated)**:
    *   **Dataform**: `definitions/3_gold/`.
    *   **Goal**: Aggregated stats, business-level metrics, and views ready for dashboarding.

### Coding Standards
*   **General**: Follow Industry Best Practices. Keep code DRY (Don't Repeat Yourself), Clean, and Modular.
*   **Python**: Follow **PEP 8** style guidelines.
*   **SQL**: Use standard SQL formatting. Upper-case keywords, lower-case identifiers.
*   **HTML/CSS**: Use Semantic HTML tags. CSS should be organized and specific.
*   **Commits**: Use conventional commit messages if possible.

---

## 4. Development Workflow

### Prerequisites

To work on this repository, you must have the following tools installed:

1.  **[Python 3.9+](https://www.python.org/downloads/)**: For backend development.
2.  **[Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install)**: For interacting with GCP resources.
3.  **[HashiCorp Terraform](https://developer.hashicorp.com/terraform/downloads)**: For infrastructure management.
4.  **[Node.js](https://nodejs.org/)**: (Optional) Only required if you want to run Dataform locally.

### 🛠️ Setup Instructions

#### 1. Backend (Python/Docker)
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```
*   The API will start locally at `http://localhost:8080`.

#### 2. Frontend (Static)
*   Simply open `frontend/index.html` in your browser.
*   For development, you can use a simple HTTP server:
    ```bash
    cd frontend
    python -m http.server 3000
    ```

#### 3. Dataform (Pipeline)
*   **Primary Execution**: Dataform runs automatically via **GitHub Actions** whenever code is pushed to the `main` branch.
*   **Optional Local Development**:
    ```bash
    cd data
    npm install -g @dataform/cli
    dataform compile # Check for errors
    dataform run     # Execute against BigQuery
    ```
*   **Note**: You need `~/.config/gcloud/application_default_credentials.json` setup via `gcloud auth application-default login`.

#### 4. Infrastructure (Terraform)
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

---

## 5. Deployment & Secrets

### GitHub Actions Secrets
The following secrets MUST be configured in the GitHub Repository settings for CI/CD to work:

| Secret Name | Description | Required By |
| :--- | :--- | :--- |
| **`WIF_PROVIDER`** | The full GCP resource name of the Workload Identity Provider. | `deploy_backend.yaml`, `dataform.yaml` |
| **`WIF_SERVICE_ACCOUNT`** | The Service Account email that GitHub Actions impersonates. | `deploy_backend.yaml`, `dataform.yaml` |
| **`GCP_PROJECT_ID`** | The Google Cloud Project ID (e.g., `victory-discipleship`). | `deploy_backend.yaml` |
| **`GCP_CREDENTIALS`** | (Optional/Legacy) Raw JSON Service Account key. Prefer WIF where possible. | `deploy_backend.yaml` |

### Deployment Targets
*   **Backend**: Automatically deployed to **Cloud Run** on pushing to `main` (if changes are in `backend/`).
*   **Frontend**: Deployed to **Cloudflare Pages** (configured via Cloudflare Dashboard linked to this repo).
*   **Data Pipeline**: Compiled and run via **Dataform CLI** on pushing to `main` (if changes are in `data/`).

---

> [!NOTE]
> **Troubleshooting Tip**: If the backend fails to deploy, check the `WIF_PROVIDER` and `WIF_SERVICE_ACCOUNT` secrets first. Ensure the Service Account has the `roles/run.developer` and `roles/iam.serviceAccountUser` roles.