# Declare Azure SQL Database Server
resource "azurerm_mssql_server" "db_server" {
    name = "sqlserver${var.project_name}"
    resource_group_name = var.resource_group_name
    location = var.location
    version = "12.0"
    administrator_login = var.admin_username
    administrator_login_password = var.admin_password
    minimum_tls_version = 1.2 
}

resource "azurerm_mssql_database" "db" {
    name = "mssql-db"
    server_id = azurerm_mssql_server.db_server.id
    sku_name     = "S0"
    collation    = "SQL_Latin1_General_CP1_CI_AS"
    max_size_gb  = 2
}

resource "azurerm_mssql_virtual_network_rule" "db-rule" {
    name = "mssql-vnet-rule"
    server_id = azurerm_mssql_server.db_server.id
    subnet_id = var.subnet_id
}