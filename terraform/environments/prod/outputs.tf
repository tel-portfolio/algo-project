output "resource_group_name" {
  value = module.networking.rg_name
}

output "sql_server_fqdn" {
  value = "mssqlserver.database.windows.net" 
}

output "key_vault_name" {
  value = module.security.key_vault_name
}

output "acr_login_server" {
  value = module.compute.acr_login_server
}