variable "project"      { description = "GCP project ID" }
variable "region"       { default = "us-east4" }
variable "zone"         { default = "us-east4-a" }
variable "cluster_name" { default = "fastapi-demo-cluster" }
variable "subnet_cidr"  { default = "10.30.0.0/20" }
variable "pods_cidr"    { default = "10.40.0.0/16" }
variable "services_cidr"{ default = "10.50.0.0/16" }
variable "master_cidr"  { default = "10.60.0.0/28" }
variable "machine_type" { default = "e2-standard-2" }
variable "node_count"   { default = 2; type = number }
variable "node_min"     { default = 2; type = number }
variable "node_max"     { default = 8; type = number }
variable "environment"  { default = "production" }
