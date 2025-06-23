# Create Service Principal for Docker Authentication
# This script creates a Service Principal that can be used for authentication in Docker containers
# az ad sp delete --id ae111875-de37-4a2c-8af6-3f93e10634f9
param(
    [Parameter(Mandatory=$true)]
    [string]$ServicePrincipalName,
    
    [string]$SubscriptionId = $null
)

Write-Host "Creating Service Principal for Docker Authentication..." -ForegroundColor Green

# Check if Azure CLI is installed
try {
    $azVersion = az version --query "azure-cli-version" -o tsv 2>$null
    if ($azVersion) {
        Write-Host "Azure CLI version: $azVersion" -ForegroundColor Blue
    }
} catch {
    Write-Host "ERROR: Azure CLI not found. Please install it first: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Red
    exit 1
}

# Check login status
Write-Host "Checking Azure login status..." -ForegroundColor Yellow
$currentAccountJson = az account show --output json 2>$null
if (-not $currentAccountJson) {
    Write-Host "ERROR: Please login to Azure first:" -ForegroundColor Red
    Write-Host "az login" -ForegroundColor Cyan
    exit 1
}

$currentAccount = $currentAccountJson | ConvertFrom-Json
Write-Host "SUCCESS: Logged in as: $($currentAccount.user.name)" -ForegroundColor Green

# Set subscription if provided
if ($SubscriptionId) {
    Write-Host "Setting subscription to: $SubscriptionId" -ForegroundColor Yellow
    az account set --subscription $SubscriptionId
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to set subscription. Please check the subscription ID." -ForegroundColor Red
        exit 1
    }
}

$currentSub = az account show --query '{name:name, id:id}' -o json | ConvertFrom-Json
Write-Host "Current subscription: $($currentSub.name) ($($currentSub.id))" -ForegroundColor Blue

# Create Service Principal
Write-Host ""
Write-Host "Creating Service Principal..." -ForegroundColor Yellow
$spCommand = "az ad sp create-for-rbac --name `"$ServicePrincipalName`" --role contributor --scopes /subscriptions/$($currentSub.id) --output json"
$spJson = Invoke-Expression $spCommand

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create Service Principal. Check if the name already exists or you have permissions." -ForegroundColor Red
    exit 1
}

$sp = $spJson | ConvertFrom-Json

Write-Host ""
Write-Host "SUCCESS: Service Principal created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Add these to your .env file:" -ForegroundColor Blue
Write-Host "AZURE_CLIENT_ID=$($sp.appId)" -ForegroundColor White
Write-Host "AZURE_CLIENT_SECRET=$($sp.password)" -ForegroundColor White
Write-Host "AZURE_TENANT_ID=$($sp.tenant)" -ForegroundColor White
Write-Host "SUBSCRIPTION_ID=$($currentSub.id)" -ForegroundColor White

Write-Host ""
Write-Host "IMPORTANT SECURITY NOTES:" -ForegroundColor Yellow
Write-Host "1. Store the client secret securely - it won't be shown again" -ForegroundColor White
Write-Host "2. Consider using Azure Key Vault for production environments" -ForegroundColor White
Write-Host "3. The Service Principal has Contributor role on the entire subscription" -ForegroundColor White

Write-Host ""
Write-Host "For Docker deployment:" -ForegroundColor Cyan
Write-Host "1. Add the above variables to your .env file" -ForegroundColor White
Write-Host "2. Rebuild your Docker image: docker build -t modelselectionchat:latest ." -ForegroundColor White
Write-Host "3. Run with: docker run -p 8501:8501 --env-file .env modelselectionchat:latest" -ForegroundColor White

Write-Host ""
Write-Host "To delete this Service Principal later:" -ForegroundColor Red
Write-Host "az ad sp delete --id $($sp.appId)" -ForegroundColor Gray
