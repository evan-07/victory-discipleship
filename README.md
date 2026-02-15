# Victory Discipleship Member Management System

> [!IMPORTANT]
> **AI Agent Instructions**: This README is the **single source of truth** for this repository. When analyzing the codebase, troubleshooting, or planning changes, **ALWAYS** check this document first to understand the directory structure, architectural patterns, and deployment workflows.

## 1. Project Overview

The **Victory Discipleship Member Management System** is a full-stack application designed to manage church member data. It ingests data from a public-facing website, processes it through a data warehouse pipeline, and creates actionable insights.

### Technology Stack

*   **Frontend**: Vanilla HTML/CSS/JavaScript. Hosted on **Cloudflare Pages** for free global CDN and DDoS protection.
*   **Backend**: Python (FastAPI) running on **Google Cloud Run**. Scales to zero for 100% cost efficiency when idle.
*   **Data Warehouse**: Google BigQuery, utilizing Free Tier limits (10GB storage / 1TB query per month).
*   **Data Pipeline**: **Dataform** (using SQLX) following the **Medallion Architecture** (Bronze $\rightarrow$ Silver $\rightarrow$ Gold).
*   **Visualization**: **Looker Studio**. Native BigQuery connection, utilizing cached queries for cost control.
*   **Infrastructure**: **Terraform** for Infrastructure-as-Code (IaC) on Google Cloud Platform (GCP).
*   **Security & WAF**: **Cloudflare WAF** with Bot Fight Mode enabled to protect backend resources.
*   **CI/CD**: GitHub Actions with **Workload Identity Federation (WIF)** for secure, keyless authentication.

---

## 2. Architecture & Standards

> [!NOTE]
> For a detailed breakdown of the **Medallion Architecture**, **Technology Stack**, and **Governance Rules**, please refer to the [ARCHITECTURE.md](ARCHITECTURE.md) file.

### Repository Map

```mermaid
graph TD;
    root[Root] --> backend[backend/];
    root --> frontend[frontend/];
    root --> data[data/];
    root --> terraform[terraform/];
    
    backend --> py[main.py];
    frontend --> html[index.html];
    data --> definitions[definitions/];
    terraform --> main_tf[main.tf];
```

For a detailed file-by-file breakdown, see [ARCHITECTURE.md#4-repository-map--directory-structure](ARCHITECTURE.md#4-repository-map--directory-structure).

---

## 5. Development Workflow

### Prerequisites

To work on this repository, you must have the following tools installed:

1.  **[Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install)**: For interacting with GCP resources.
3.  **[HashiCorp Terraform](https://developer.hashicorp.com/terraform/downloads)**: For infrastructure management.

### 🛠️ Setup Instructions

#### 1. Backend (FastAPI)
*   **Exclusive Execution**: The backend runs exclusively on **Google Cloud Run**. Local execution of the API is prohibited to maintain environment parity and security.
*   **Deployment**: Automated via GitHub Actions on every push to `main` that modifies the `backend/` directory.

#### 2. Frontend
*   Simply open `frontend/index.html` in your browser.
*   For development, you can use a simple HTTP server:
    ```bash
    cd frontend
    python -m http.server 3000
    ```

#### 3. Dataform (Pipeline)
*   **Exclusive Execution**: Dataform runs exclusively via **GitHub Actions** whenever code is pushed to the `main` branch or a Pull Request is created.
*   **Validation**: Schema validation and compilation checks are performed automatically in the `Compile Dataform` job of the CI/CD pipeline. No local installation of the Dataform CLI is required.

#### 4. Infrastructure (Terraform)
*   **Local Validation**: You can use Terraform locally for linting and planning only.
    ```bash
    cd terraform
    terraform init
    terraform plan
    ```
*   **Exclusive Execution**: `terraform apply` is **strictly prohibited** locally. Infrastructure changes are applied exclusively via GitHub Actions upon merging to the `main` branch.

---

## 6. Deployment & Secrets

### GitHub Actions Secrets
The following secrets MUST be configured in the GitHub Repository settings for CI/CD to work:

| Secret Name | Description | Required By |
| :--- | :--- | :--- |
| **`WIF_PROVIDER`** | The full GCP resource name of the Workload Identity Provider. | `dataform.yaml` |
| **`WIF_SERVICE_ACCOUNT`** | The Service Account email that GitHub Actions impersonates. | `dataform.yaml` |
| **`GCP_PROJECT_ID`** | The Google Cloud Project ID (e.g., `victory-discipleship`). | `deploy_backend.yaml`, `dataform.yaml` |
| **`GCP_CREDENTIALS`** | Raw JSON Service Account key. | `deploy_backend.yaml` |
| **`GCP_LOCATION`** | The Google Cloud location (e.g., `asia-southeast1`). | `dataform.yaml` |

### Deployment Targets
*   **Backend**: Automatically deployed to **Cloud Run** on pushing to `main` (if changes are in `backend/`). Can be manually triggered via **Workflow Dispatch**.
*   **Frontend**: Deployed to **Cloudflare Pages** (configured via Cloudflare Dashboard linked to this repo).
*   **Data Pipeline**: Compiled on Pull Requests. Runs via **GitHub Actions** on pushing to `main` (if changes are in `data/`). This is the **only** environment where Dataform is executed.

---

> [!NOTE]
> **Troubleshooting Tip**: If the backend fails to deploy, check the `WIF_PROVIDER` and `WIF_SERVICE_ACCOUNT` secrets first. Ensure the Service Account has the `roles/run.developer` and `roles/iam.serviceAccountUser` roles.