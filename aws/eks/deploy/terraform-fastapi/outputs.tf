output "cluster_name"     { value = aws_eks_cluster.fastapi.name }
output "cluster_endpoint" { value = aws_eks_cluster.fastapi.endpoint }
output "cluster_version"  { value = aws_eks_cluster.fastapi.version }
output "oidc_issuer"      { value = aws_eks_cluster.fastapi.identity[0].oidc[0].issuer }
output "ecr_repository_url" { value = aws_ecr_repository.fastapi.repository_url }
output "vpc_id"           { value = aws_vpc.fastapi.id }

output "configure_kubectl" {
  description = "Run this command to configure kubectl"
  value       = "aws eks update-kubeconfig --name ${aws_eks_cluster.fastapi.name} --region ${var.region}"
}
