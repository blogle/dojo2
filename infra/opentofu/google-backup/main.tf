provider "google" {
  project = var.project_id
}

resource "google_project_service" "drive" {
  project            = var.project_id
  service            = "drive.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "iam" {
  project            = var.project_id
  service            = "iam.googleapis.com"
  disable_on_destroy = false
}

resource "google_service_account" "backup" {
  project      = var.project_id
  account_id   = var.service_account_id
  display_name = "dojo backup"
  description  = "Deployment-specific identity for encrypted dojo backups"

  depends_on = [google_project_service.iam]
}
