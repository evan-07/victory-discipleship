terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = "victory-discipleship"
  region  = "asia-southeast1"
}

# Enable required APIs
resource "google_project_service" "iam_credentials" {
  service = "iamcredentials.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "sts" {
  service = "sts.googleapis.com"
  disable_on_destroy = false
}

# Service Account for GitHub Actions
resource "google_service_account" "github_actions" {
  account_id   = "dataform-ci-sa"
  display_name = "Dataform CI Service Account"
}

# Grant Permissions to Service Account
resource "google_project_iam_member" "bigquery_admin" {
  project = "victory-discipleship"
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "dataform_editor" {
  project = "victory-discipleship"
  role    = "roles/dataform.editor"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Workload Identity Pool
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Identity pool for GitHub Actions"
}

# Workload Identity Provider
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Actions Provider"
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }
  attribute_condition = "assertion.repository == 'evan-07/victory-discipleship'"
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Allow GitHub Actions to Impersonate Service Account
resource "google_service_account_iam_member" "workload_identity_user" {
  service_account_id = google_service_account.github_actions.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/evan-07/victory-discipleship"
}
