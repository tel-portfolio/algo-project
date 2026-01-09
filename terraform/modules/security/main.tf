# Data block
data "azurerm_client_config" "current" {}

# Create Managed Identity
resource "azurerm_user_assigned_identity" "userid" {
    location = var.location
    name = "id-${var.project_name}"
    resource_group_name = var.resource_group_name
}

#Create Key Vault
resource "azurerm_key_vault" "kv" {
    name = "kv-${var.project_name}"
    location = var.location
    resource_group_name = var.resource_group_name
    enabled_for_disk_encryption = true
    tenant_id = data.azurerm_client_config.current.tenant_id
    soft_delete_retention_days = 7
    purge_protection_enabled = false  # Typically I would turn purge protection on but in a portfolio project I need to be able to purge
    sku_name = "standard"

    # Declare Access Policy for Admin
    access_policy {
        tenant_id = data.azurerm_client_config.current.tenant_id
        object_id = data.azurerm_client_config.current.object_id
        secret_permissions = ["Get", "List", "Set", "Delete", "Purge"]
    }

    # Declare Access Policy for Service Principal
    access_policy {
        tenant_id = data.azurerm_client_config.current.tenant_id
        object_id = azurerm_user_assigned_identity.userid.principal_id
        secret_permissions = ["Get", "List"]
    }
}

output "key_vault_id" { value = azurerm_key_vault.kv.id }
output "key_vault_name" { value = azurerm_key_vault.kv.name }
output "identity_id" { value = azurerm_user_assigned_identity.userid.id }
output "identity_principal_id" { value = azurerm_user_assigned_identity.userid.principal_id }