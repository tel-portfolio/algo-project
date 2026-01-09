variable "resource_group_name" {
  type        = string
  description = "Resource group name"
}

variable "location" {
  type        = string
  description = "Azure region."
}

variable "project_name" {
  type        = string
  description = "Name of the project."
}

variable "admin_username" {
  type        = string
  description = "SQL server username"
  default     = "sqladmin"
}

variable "admin_password" {
  type        = string
  description = "SQL server password"
  sensitive   = true 
}

variable "subnet_id" {
  type        = string
  description = "Subnet ID from Networking module"
}