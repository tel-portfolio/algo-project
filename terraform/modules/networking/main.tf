# Resource Group
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

# Declare Virtual Network
resource "azurerm_virtual_network" "vnet" {
    name = "algo_vnet"
    location = azurerm_resource_group.rg.location
    resource_group_name = azurerm_resource_group.rg.name
    address_space = ["10.0.0.0/16"]
}

# VM Subnet
resource "azurerm_subnet" "subnet" {
  name                 = "snet-compute"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]

  #Service Enpoints
  service_endpoints = [
    "Microsoft.Sql",
    "Microsoft.Storage",
    "Microsoft.KeyVault",
    "Microsoft.ContainerRegistry"
  ]
}

# Outputs
output "rg_name" {value = azurerm_resource_group.rg.name}
output "rg_location" {value = azurerm_resource_group.rg.location}
output "subnet_id" {value = azurerm_subnet.subnet.id}
output "vnet_id" {value = azurerm_virtual_network.vnet.id}