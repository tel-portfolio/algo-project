resource "azurerm_storage_account" "storageac" {
    name = "algostacc43hg0t"
    location = var.location
    resource_group_name = var.resource_group_name
    account_tier = "Standard"
    account_replication_type = "LRS"
    min_tls_version = "TLS1_2"
}

resource "azurerm_storage_container" "storagecontainer" {
  name                  = "algologs"
  storage_account_name    = azurerm_storage_account.storageac.name
  container_access_type = "private"
}