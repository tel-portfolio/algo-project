# Log in 
Connect-AzAccount

# Set Variables
$ResourceGroupName = "rg-tfstate"
$Location = "WestUS2"
# Create a random unique name for the storage account
$StorageAccountName = "tfstate" + (Get-Random -Minimum 10000 -Maximum 99999)
$ContainerName = "tfstate"

# Create Resource Group
New-AzResourceGroup -Name $ResourceGroupName -Location $Location

# Create Storage Account
$StorageAccount = New-AzStorageAccount -ResourceGroupName $ResourceGroupName -Name $StorageAccountName -SkuName Standard_LRS -Location $Location

# Create Container
$Context = $StorageAccount.Context
New-AzStorageContainer -Name $ContainerName -Context $Context

# Retrieve and print Access Key
$Key = (Get-AzStorageAccountKey -ResourceGroupName $ResourceGroupName -Name $StorageAccountName)[0].Value

Write-Host "-----------------------------" 
Write-Host "Storage Account Name: $StorageAccountName"
Write-Host "Access Key: $Key"
Write-Host "-----------------------------"