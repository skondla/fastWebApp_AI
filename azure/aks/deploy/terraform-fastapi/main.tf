# ──────────────────────────────────────────────────────────────────────────────
# FastAPI USER App — Azure AKS Terraform
# Provisions: Resource Group → VNet → AKS Cluster → ACR → Workload Identity
# ──────────────────────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.47"
    }
  }
}

provider "azurerm" {
  features {}
}

# ─── Resource Group ───────────────────────────────────────────────────────────
resource "azurerm_resource_group" "fastapi" {
  name     = var.resource_group_name
  location = var.location
  tags = {
    Project     = "fastapi-user-app"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ─── Virtual Network ──────────────────────────────────────────────────────────
resource "azurerm_virtual_network" "fastapi" {
  name                = "${var.cluster_name}-vnet"
  resource_group_name = azurerm_resource_group.fastapi.name
  location            = azurerm_resource_group.fastapi.location
  address_space       = [var.vnet_cidr]
}

resource "azurerm_subnet" "aks" {
  name                 = "${var.cluster_name}-aks-subnet"
  resource_group_name  = azurerm_resource_group.fastapi.name
  virtual_network_name = azurerm_virtual_network.fastapi.name
  address_prefixes     = [var.subnet_cidr]
}

# ─── Azure Container Registry ─────────────────────────────────────────────────
resource "azurerm_container_registry" "fastapi" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.fastapi.name
  location            = azurerm_resource_group.fastapi.location
  sku                 = "Standard"
  admin_enabled       = false

  # Enable vulnerability scanning (Defender for Containers)
  retention_policy {
    days    = 30
    enabled = true
  }
}

# ─── AKS Cluster ──────────────────────────────────────────────────────────────
resource "azurerm_kubernetes_cluster" "fastapi" {
  name                = var.cluster_name
  location            = azurerm_resource_group.fastapi.location
  resource_group_name = azurerm_resource_group.fastapi.name
  dns_prefix          = var.cluster_name
  kubernetes_version  = var.kubernetes_version

  # ── Default node pool ────────────────────────────────────────────────
  default_node_pool {
    name                = "system"
    node_count          = var.system_node_count
    vm_size             = var.system_vm_size
    vnet_subnet_id      = azurerm_subnet.aks.id
    os_disk_size_gb     = 50
    type                = "VirtualMachineScaleSets"
    enable_auto_scaling = true
    min_count           = 1
    max_count           = 3
    upgrade_settings {
      max_surge = "33%"
    }
  }

  # ── Workload Identity (replaces pod identity) ────────────────────────
  identity { type = "SystemAssigned" }
  workload_identity_enabled = true
  oidc_issuer_enabled       = true

  # ── Networking ───────────────────────────────────────────────────────
  network_profile {
    network_plugin     = "azure"
    network_policy     = "calico"
    load_balancer_sku  = "standard"
    service_cidr       = "10.100.0.0/16"
    dns_service_ip     = "10.100.0.10"
  }

  # ── Add-ons ──────────────────────────────────────────────────────────
  azure_policy_enabled = true

  # ── Security: private cluster option ─────────────────────────────────
  # private_cluster_enabled = true  # Uncomment for private endpoint
  local_account_disabled = false

  # ── Logging ──────────────────────────────────────────────────────────
  azure_active_directory_role_based_access_control {
    managed            = true
    azure_rbac_enabled = true
  }

  tags = {
    Project     = "fastapi-user-app"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ── User node pool for app workloads ─────────────────────────────────────────
resource "azurerm_kubernetes_cluster_node_pool" "app" {
  name                  = "app"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.fastapi.id
  vm_size               = var.app_vm_size
  node_count            = var.app_node_count
  enable_auto_scaling   = true
  min_count             = var.app_node_min
  max_count             = var.app_node_max
  vnet_subnet_id        = azurerm_subnet.aks.id
  os_disk_size_gb       = 50
  tags = { role = "app" }
}

# ─── Attach ACR to AKS ───────────────────────────────────────────────────────
resource "azurerm_role_assignment" "aks_acr_pull" {
  principal_id                     = azurerm_kubernetes_cluster.fastapi.kubelet_identity[0].object_id
  role_definition_name             = "AcrPull"
  scope                            = azurerm_container_registry.fastapi.id
  skip_service_principal_aad_check = true
}
