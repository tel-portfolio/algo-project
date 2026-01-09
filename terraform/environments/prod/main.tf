terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }

backend "azurerm" {
    resource_group_name  = "rg-tfstate"
    storage_account_name = "tfstate38213" # (Your storage account name)
    container_name       = "tfstate"
    key                  = "prod.terraform.tfstate" #(Set this key as an environment variable with -- export ARM_ACCESS_KEY="<YOUR_STORAGE_ACCESS_KEY>" )
  }
}

provider "azurerm" {
    features {
        key_vault {
            purge_soft_delete_on_destroy = true # for a portfolio project it makes sense to clean up the soft delete when destroyed
        }
    }
}

# Networking
module "networking" {
    source = "../../modules/networking"
    resource_group_name = "algo-trading-portfolio-project"
    location = "West US 2"
    project_name = "algoportfolioproject"
}

# Key Vault
module "security" {
    source = "../../modules/security"
    resource_group_name = module.networking.rg_name
    location = module.networking.rg_location
    project_name        = "algoportfolioproject"
}

# Database
module "database" {
    source = "../../modules/database"
    resource_group_name = module.networking.rg_name
    location = module.networking.rg_location
    project_name        = "algoportfolioproject"

    #Subnet ID from Networking Module
    subnet_id           = module.networking.subnet_id

    # Secrets
    admin_username      = "sqladmin"
    admin_password      = var.db_password
}

# Azure Container Registry
module "compute" {
  source              = "../../modules/compute"
  resource_group_name = module.networking.rg_name
  location            = module.networking.rg_location
  project_name        = "algoportfolioproject"
  environment         = "prod"
}

# Storage Account
module "storage" {
  source = "../../modules/storage"
  resource_group_name = module.networking.rg_name
  location = module.networking.rg_location
}