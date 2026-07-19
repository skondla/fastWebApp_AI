# ──────────────────────────────────────────────────────────────────────────────
# FastAPI USER App — GCP GKE Terraform
# Provisions: VPC → Private GKE Cluster → Node Pool → Artifact Registry → IAM
# ──────────────────────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project
  region  = var.region
}

provider "google-beta" {
  project = var.project
  region  = var.region
}

# ─── VPC ──────────────────────────────────────────────────────────────────────
resource "google_compute_network" "fastapi" {
  name                    = "${var.cluster_name}-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "fastapi" {
  name          = "${var.cluster_name}-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.fastapi.id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = var.pods_cidr
  }
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = var.services_cidr
  }

  private_ip_google_access = true
}

resource "google_compute_router" "fastapi" {
  name    = "${var.cluster_name}-router"
  region  = var.region
  network = google_compute_network.fastapi.id
}

resource "google_compute_router_nat" "fastapi" {
  name                               = "${var.cluster_name}-nat"
  router                             = google_compute_router.fastapi.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

# ─── GKE Cluster ──────────────────────────────────────────────────────────────
resource "google_container_cluster" "fastapi" {
  name     = var.cluster_name
  location = var.zone

  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.fastapi.id
  subnetwork = google_compute_subnetwork.fastapi.id

  # ── Private cluster ──────────────────────────────────────────────────
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = var.master_cidr
  }

  # ── Networking ───────────────────────────────────────────────────────
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  # ── Security ─────────────────────────────────────────────────────────
  workload_identity_config {
    workload_pool = "${var.project}.svc.id.goog"
  }

  release_channel {
    channel = "REGULAR"
  }

  # Binary Authorization
  binary_authorization {
    evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
  }

  # Shield GKE nodes
  enable_shielded_nodes = true

  # ── Logging & Monitoring ─────────────────────────────────────────────
  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"

  resource_labels = {
    project     = "fastapi-user-app"
    environment = var.environment
    managed_by  = "terraform"
  }
}

# ─── Node Pool ────────────────────────────────────────────────────────────────
resource "google_container_node_pool" "fastapi" {
  name       = "${var.cluster_name}-app-pool"
  location   = var.zone
  cluster    = google_container_cluster.fastapi.name
  node_count = var.node_count

  autoscaling {
    min_node_count = var.node_min
    max_node_count = var.node_max
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    machine_type = var.machine_type
    disk_type    = "pd-ssd"
    disk_size_gb = 50

    # ── Workload Identity per node ────────────────────────────────────
    workload_metadata_config { mode = "GKE_METADATA" }

    # ── Shielded nodes ────────────────────────────────────────────────
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]

    labels = {
      role = "app"
    }
  }

  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }
}

# ─── Artifact Registry ────────────────────────────────────────────────────────
resource "google_artifact_registry_repository" "fastapi" {
  provider      = google-beta
  location      = var.region
  repository_id = "fastapi-user-app"
  format        = "DOCKER"
  description   = "FastAPI USER app container images"

  cleanup_policies {
    id     = "keep-last-10"
    action = "KEEP"
    most_recent_versions {
      keep_count = 10
    }
  }
}

# ─── Service Account (Workload Identity) ──────────────────────────────────────
resource "google_service_account" "fastapi" {
  account_id   = "${var.cluster_name}-sa"
  display_name = "FastAPI App Workload Identity SA"
}

# Allow the K8s service account to impersonate the GSA
resource "google_service_account_iam_member" "workload_identity" {
  service_account_id = google_service_account.fastapi.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project}.svc.id.goog[fastapi-namespace/fastapi-sa]"
}

# Grant pull access to GAR
resource "google_artifact_registry_repository_iam_member" "fastapi_reader" {
  provider   = google-beta
  location   = google_artifact_registry_repository.fastapi.location
  repository = google_artifact_registry_repository.fastapi.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.fastapi.email}"
}
