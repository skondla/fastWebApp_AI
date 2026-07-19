variable "location"            { default = "eastus2" }
variable "resource_group_name" { default = "fastapi-rg" }
variable "cluster_name"        { default = "fastapi-aks-cluster" }
variable "kubernetes_version"  { default = "1.29" }
variable "vnet_cidr"           { default = "10.20.0.0/16" }
variable "subnet_cidr"         { default = "10.20.1.0/24" }
variable "acr_name"            { default = "fastapiregistry" }
variable "system_node_count"   { default = 1; type = number }
variable "system_vm_size"      { default = "Standard_D2s_v3" }
variable "app_vm_size"         { default = "Standard_D4s_v3" }
variable "app_node_count"      { default = 2; type = number }
variable "app_node_min"        { default = 2; type = number }
variable "app_node_max"        { default = 8; type = number }
variable "environment"         { default = "production" }
