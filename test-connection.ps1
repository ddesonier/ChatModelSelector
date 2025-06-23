# Test Azure OpenAI Connection Script
# This script tests your Azure OpenAI configuration without running the full Streamlit app

param(
    [string]$EnvFile = ".env"
)

Write-Host "🔍 Testing Azure OpenAI Connection..." -ForegroundColor Green

# Check if .env file exists
if (-not (Test-Path $EnvFile)) {
    Write-Host "❌ .env file not found. Please create one based on .env.example" -ForegroundColor Red
    exit 1
}

# Load environment variables from .env file
Write-Host "📄 Loading environment variables from $EnvFile..." -ForegroundColor Yellow
$envContent = Get-Content $EnvFile
foreach ($line in $envContent) {
    if ($line -and $line.Trim() -and -not $line.StartsWith("#")) {
        $parts = $line.Split("=", 2)
        if ($parts.Count -eq 2) {
            $name = $parts[0].Trim()
            $value = $parts[1].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
            Write-Host "  ✓ $name" -ForegroundColor Gray
        }
    }
}

# Get environment variables
$endpoint = $env:AZURE_OPENAI_ENDPOINT
$apikey = $env:AZURE_OPENAI_KEY
$apiversion = if ($env:AZURE_OPENAI_API_VERSION) { $env:AZURE_OPENAI_API_VERSION } else { "2024-06-01" }
$subscriptionId = $env:SUBSCRIPTION_ID
$resourceGroup = $env:RESOURCE_GROUP_NAME
$accountName = $env:AOAI_ACCOUNT_NAME

Write-Host "" 
Write-Host "📋 Configuration Check:" -ForegroundColor Blue
if ($endpoint) {
    $maskedEndpoint = $endpoint.Substring(0, [Math]::Min(30, $endpoint.Length)) + "..."
    Write-Host "  Endpoint: $maskedEndpoint" -ForegroundColor White
} else {
    Write-Host "  Endpoint: NOT SET" -ForegroundColor Red
}

if ($apikey) {
    Write-Host "  API Key: ***...$(if($apikey.Length -gt 4) { $apikey.Substring($apikey.Length - 4) } else { "***" })" -ForegroundColor White
} else {
    Write-Host "  API Key: NOT SET" -ForegroundColor Red
}

Write-Host "  API Version: $apiversion" -ForegroundColor White
Write-Host "  Subscription: $(if($subscriptionId) { $subscriptionId } else { 'NOT SET' })" -ForegroundColor $(if($subscriptionId) { 'White' } else { 'Red' })
Write-Host "  Resource Group: $(if($resourceGroup) { $resourceGroup } else { 'NOT SET' })" -ForegroundColor $(if($resourceGroup) { 'White' } else { 'Red' })
Write-Host "  Account Name: $(if($accountName) { $accountName } else { 'NOT SET' })" -ForegroundColor $(if($accountName) { 'White' } else { 'Red' })

# Check for missing variables
$missing = @()
if (-not $endpoint) { $missing += "AZURE_OPENAI_ENDPOINT" }
if (-not $apikey) { $missing += "AZURE_OPENAI_KEY" }
if (-not $subscriptionId) { $missing += "SUBSCRIPTION_ID" }
if (-not $resourceGroup) { $missing += "RESOURCE_GROUP_NAME" }
if (-not $accountName) { $missing += "AOAI_ACCOUNT_NAME" }

if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "❌ Missing required environment variables:" -ForegroundColor Red
    foreach ($var in $missing) {
        Write-Host "  - $var" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "💡 Run .\discover-azure-resources.ps1 to find the correct values" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "✅ All environment variables are set" -ForegroundColor Green

# Test Azure CLI login
Write-Host ""
Write-Host "🔐 Testing Azure CLI authentication..." -ForegroundColor Yellow
$azCommand = "az account show --output json"
$currentAccountJson = Invoke-Expression $azCommand 2>$null
if ($currentAccountJson) {
    $currentAccount = $currentAccountJson | ConvertFrom-Json
    Write-Host "  ✓ Logged in as: $($currentAccount.user.name)" -ForegroundColor Green
    Write-Host "  ✓ Current subscription: $($currentAccount.name)" -ForegroundColor Green
    
    if ($currentAccount.id -ne $subscriptionId) {
        Write-Host "  ⚠️  Warning: Current subscription ($($currentAccount.id)) doesn't match .env subscription ($subscriptionId)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ❌ Not logged in to Azure CLI. Run: az login" -ForegroundColor Red
    exit 1
}

# Test resource existence
Write-Host ""
Write-Host "🔍 Testing Azure OpenAI resource existence..." -ForegroundColor Yellow
$resourceCommand = "az cognitiveservices account show --name `"$accountName`" --resource-group `"$resourceGroup`" --output json"
$resourceJson = Invoke-Expression $resourceCommand 2>$null
if ($resourceJson) {
    $resource = $resourceJson | ConvertFrom-Json
    Write-Host "  ✓ Resource found: $($resource.name)" -ForegroundColor Green
    Write-Host "  ✓ Location: $($resource.location)" -ForegroundColor Green
    Write-Host "  ✓ Status: $($resource.properties.provisioningState)" -ForegroundColor Green
} else {
    Write-Host "  ❌ Azure OpenAI resource '$accountName' not found in resource group '$resourceGroup'" -ForegroundColor Red
    Write-Host "  💡 Run this to see available resources:" -ForegroundColor Yellow
    Write-Host "     az cognitiveservices account list --query `"[?kind=='OpenAI']`" --output table" -ForegroundColor Cyan
    exit 1
}

# Test deployments
Write-Host ""
Write-Host "🚀 Testing model deployments..." -ForegroundColor Yellow
$deploymentCommand = "az cognitiveservices account deployment list --name `"$accountName`" --resource-group `"$resourceGroup`" --output json"
$deploymentsJson = Invoke-Expression $deploymentCommand 2>$null
if ($deploymentsJson) {
    $deployments = $deploymentsJson | ConvertFrom-Json
    if ($deployments -and $deployments.Count -gt 0) {
        Write-Host "  ✅ Found $($deployments.Count) deployment(s):" -ForegroundColor Green
        foreach ($deployment in $deployments) {
            Write-Host "    - $($deployment.name) (Model: $($deployment.properties.model.name))" -ForegroundColor White
        }
    } else {
        Write-Host "  ⚠️  No deployments found. You need to create model deployments." -ForegroundColor Yellow
        Write-Host "  💡 Go to Azure Portal → Your OpenAI Resource → Model deployments → Create new deployment" -ForegroundColor Cyan
    }
} else {
    Write-Host "  ❌ Failed to retrieve deployments" -ForegroundColor Red
    Write-Host "  💡 Check your permissions on the resource" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Connection test completed!" -ForegroundColor Green
Write-Host "If you see any errors above, fix them before running the Streamlit app." -ForegroundColor White
