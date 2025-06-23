# Azure OpenAI Resource Discovery Script
# This script helps you find your Azure OpenAI resources and their details

Write-Host "Discovering your Azure OpenAI resources..." -ForegroundColor Green

# Check if Azure CLI is installed
try {
    $azVersion = az version --query "azure-cli-version" -o tsv 2>$null
    if ($azVersion) {
        Write-Host "Azure CLI version: $azVersion" -ForegroundColor Blue
    }
} catch {
    Write-Host "Azure CLI not found. Please install it first: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Red
    exit 1
}

# Login check
Write-Host "Checking Azure login status..." -ForegroundColor Yellow
$loginStatus = az account show 2>$null
if (-not $loginStatus) {
    Write-Host "Please login to Azure first:" -ForegroundColor Red
    Write-Host "az login" -ForegroundColor Cyan
    exit 1
}

# Get current subscription
$currentSub = az account show --query "{name:name, id:id}" -o json | ConvertFrom-Json
Write-Host "Current subscription: $($currentSub.name) ($($currentSub.id))" -ForegroundColor Blue

# Find all Azure OpenAI resources
Write-Host "`nSearching for Azure OpenAI resources..." -ForegroundColor Yellow
$cognitiveServices = az cognitiveservices account list --query "[?kind=='OpenAI']" -o json | ConvertFrom-Json

if ($cognitiveServices.Count -eq 0) {
    Write-Host "No Azure OpenAI resources found in the current subscription." -ForegroundColor Red
    Write-Host "Please create an Azure OpenAI resource first." -ForegroundColor Yellow
    exit 1
}

Write-Host "`nFound $($cognitiveServices.Count) Azure OpenAI resource(s):" -ForegroundColor Green

foreach ($resource in $cognitiveServices) {
    Write-Host "`n--- Resource Details ---" -ForegroundColor Cyan
    Write-Host "Resource Name: $($resource.name)" -ForegroundColor White
    Write-Host "Resource Group: $($resource.resourceGroup)" -ForegroundColor White
    Write-Host "Location: $($resource.location)" -ForegroundColor White
    Write-Host "Endpoint: $($resource.properties.endpoint)" -ForegroundColor White
    
    # Get deployments for this resource
    Write-Host "Getting deployments..." -ForegroundColor Yellow
    try {
        $deployments = az cognitiveservices account deployment list --name $resource.name --resource-group $resource.resourceGroup -o json | ConvertFrom-Json
        if ($deployments.Count -gt 0) {
            Write-Host "Deployments:" -ForegroundColor Green
            foreach ($deployment in $deployments) {
                Write-Host "  - $($deployment.name) (Model: $($deployment.properties.model.name))" -ForegroundColor White
            }
        } else {
            Write-Host "No deployments found." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Could not retrieve deployments. Check permissions." -ForegroundColor Red
    }
    
    Write-Host "`nEnvironment variables for this resource:" -ForegroundColor Magenta
    Write-Host "AZURE_OPENAI_ENDPOINT=$($resource.properties.endpoint)" -ForegroundColor Gray
    Write-Host "RESOURCE_GROUP_NAME=$($resource.resourceGroup)" -ForegroundColor Gray
    Write-Host "AOAI_ACCOUNT_NAME=$($resource.name)" -ForegroundColor Gray
    Write-Host "SUBSCRIPTION_ID=$($currentSub.id)" -ForegroundColor Gray
    Write-Host "AZURE_OPENAI_API_VERSION=2024-06-01" -ForegroundColor Gray
    Write-Host "`nNote: You'll need to get the API key from the Azure portal." -ForegroundColor Yellow
}

Write-Host "`n=== Instructions ===" -ForegroundColor Green
Write-Host "1. Copy the environment variables for your desired resource to your .env file"
Write-Host "2. Get the API key from Azure portal: Resource Management > Keys and Endpoint"
Write-Host "3. Add AZURE_OPENAI_KEY=your-key-here to your .env file"
Write-Host "4. Run your application: streamlit run app.py"
