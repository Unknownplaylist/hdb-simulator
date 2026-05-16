terraform {
  required_version = ">= 1.5"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.0" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" { type = string }
variable "region"     { type = string; default = "asia-southeast1" }
variable "db_password" { type = string; sensitive = true }

resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "storage.googleapis.com",
    "compute.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "backend" {
  location      = var.region
  repository_id = "hdb-sim"
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

resource "google_sql_database_instance" "pg" {
  name             = "hdb-sim-pg"
  region           = var.region
  database_version = "POSTGRES_15"
  settings {
    tier              = "db-f1-micro"
    availability_type = "ZONAL"
    disk_size         = 10
    backup_configuration { enabled = true }
  }
  deletion_protection = false
  depends_on          = [google_project_service.apis]
}

resource "google_sql_database" "hdbsim" {
  name     = "hdbsim"
  instance = google_sql_database_instance.pg.name
}

resource "google_sql_user" "hdbsim" {
  name     = "hdbsim"
  instance = google_sql_database_instance.pg.name
  password = var.db_password
}

resource "google_storage_bucket" "data" {
  name                        = "${var.project_id}-hdb-data"
  location                    = var.region
  uniform_bucket_level_access = true
  cors {
    origin = ["*"]
    method = ["GET"]
    response_header = ["Content-Type"]
    max_age_seconds = 3600
  }
}

resource "google_storage_bucket" "frontend" {
  name                        = "${var.project_id}-hdb-frontend"
  location                    = var.region
  uniform_bucket_level_access = true
  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"
  }
}

resource "google_storage_bucket_iam_member" "data_public" {
  bucket = google_storage_bucket.data.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}
resource "google_storage_bucket_iam_member" "frontend_public" {
  bucket = google_storage_bucket.frontend.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

resource "google_cloud_run_v2_service" "api" {
  name     = "hdb-sim-api"
  location = var.region

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"
      resources {
        limits = { memory = "512Mi", cpu = "1" }
      }
    }
    volumes {
      name = "cloudsql"
      cloud_sql_instance { instances = [google_sql_database_instance.pg.connection_name] }
    }
  }
  ingress = "INGRESS_TRAFFIC_ALL"
  lifecycle {
    ignore_changes = [template[0].containers[0].image]
  }
  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.api.name
  location = google_cloud_run_v2_service.api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "api_url"           { value = google_cloud_run_v2_service.api.uri }
output "frontend_bucket"   { value = google_storage_bucket.frontend.url }
output "data_bucket"       { value = google_storage_bucket.data.url }
output "cloudsql_conn"     { value = google_sql_database_instance.pg.connection_name }
