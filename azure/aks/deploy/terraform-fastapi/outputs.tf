output "cluster_name"        { value = azurerm_kubernetes_cluster.fastapi.name }
output "cluster_fqdn"        { value = azurerm_kubernetes_cluster.fastapi.fqdn }
output "acr_login_server"    { value = azurerm_container_registry.fastapi.login_server }
output "resource_group"      { value = azurerm_resource_group.fastapi.name }
output "oidc_issuer_url"     { value = azurerm_kubernetes_cluster.fastapi.oidc_issuer_url }

output "configure_kubectl" {
  value = "az aks get-credentials --resource-group ${azurerm_resource_group.fastapi.name} --name ${azurerm_kubernetes_cluster.fastapi.name}"
}
