output "storage_account_name" {
  value = azurerm_storage_account.storageac.name
}

output "storage_account_key" {
  value = azurerm_storage_account.storageac.primary_access_key
  sensitive = true
}

output "container_name" {
  value = azurerm_storage_container.storagecontainer.name
}