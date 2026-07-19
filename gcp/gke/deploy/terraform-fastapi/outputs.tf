output "cluster_name"      { value = google_container_cluster.fastapi.name }
output "cluster_endpoint"  { value = google_container_cluster.fastapi.endpoint }
output "gar_repository"    { value = google_artifact_registry_repository.fastapi.name }
output "gsa_email"         { value = google_service_account.fastapi.email }

output "configure_kubectl" {
  value = "gcloud container clusters get-credentials ${google_container_cluster.fastapi.name} --zone ${var.zone} --project ${var.project}"
}
