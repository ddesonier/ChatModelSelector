# Check Environment Variables Script
# This script shows what environment variables are actually being loaded

param(
    [string]$EnvFile = ".env"
)

Write-Host "Checking environment variables for Docker authentication..." -ForegroundColor Green

# Check if .env file exists
if (-not (Test-Path $EnvFile)) {
    Write-Host "ERROR: .env file not found at: $EnvFile" -ForegroundColor Red
    Write-Host "Please create a .env file with your Azure credentials" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found .env file: $EnvFile" -ForegroundColor Blue
Write-Host ""

# Read and display .env file contents (masking sensitive values)
Write-Host "Environment file contents:" -ForegroundColor Yellow
$envContent = Get-Content $EnvFile
$requiredVars = @(
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_KEY", 
    "AZURE_OPENAI_API_VERSION",
    "SUBSCRIPTION_ID",
    "RESOURCE_GROUP_NAME",
    "AOAI_ACCOUNT_NAME",
    "AZURE_CLIENT_ID",
    "AZURE_CLIENT_SECRET",
    "AZURE_TENANT_ID"
)

$foundVars = @{}
$missingVars = @()

foreach ($line in $envContent) {
    if ($line -and $line.Trim() -and -not $line.StartsWith("#")) {
        $parts = $line.Split("=", 2)
        if ($parts.Count -eq 2) {
            $name = $parts[0].Trim()
            $value = $parts[1].Trim()
            
            if ($name -in $requiredVars) {
                $foundVars[$name] = $value
                
                # Mask sensitive values for display
                if ($name -like "*KEY*" -or $name -like "*SECRET*") {
                    $maskedValue = if ($value.Length -gt 8) { 
                        $value.Substring(0, 4) + "***" + $value.Substring($value.Length - 4) 
                    } else { 
                        "***" 
                    }
                    Write-Host "  $name = $maskedValue" -ForegroundColor Green
                } else {
                    Write-Host "  $name = $value" -ForegroundColor Green
                }
            }
        }
    }
}

# Check for missing required variables
foreach ($var in $requiredVars) {
    if (-not $foundVars.ContainsKey($var)) {
        $missingVars += $var
    }
}

Write-Host ""
if ($missingVars.Count -gt 0) {
    Write-Host "MISSING REQUIRED VARIABLES:" -ForegroundColor Red
    foreach ($var in $missingVars) {
        Write-Host "  - $var" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "SOLUTIONS:" -ForegroundColor Yellow
    if ("AZURE_CLIENT_ID" -in $missingVars -or "AZURE_CLIENT_SECRET" -in $missingVars -or "AZURE_TENANT_ID" -in $missingVars) {
        Write-Host "1. Create Service Principal:" -ForegroundColor Cyan
        Write-Host "   .\create-service-principal.ps1 -ServicePrincipalName 'ModelSelectorApp'" -ForegroundColor White
    }
    
    if ("AZURE_OPENAI_ENDPOINT" -in $missingVars -or "RESOURCE_GROUP_NAME" -in $missingVars -or "AOAI_ACCOUNT_NAME" -in $missingVars) {
        Write-Host "2. Discover Azure resources:" -ForegroundColor Cyan
        Write-Host "   .\discover-azure-resources.ps1" -ForegroundColor White
    }
} else {
    Write-Host "SUCCESS: All required environment variables are present!" -ForegroundColor Green
}

Write-Host ""
Write-Host "To test Docker with current .env file:" -ForegroundColor Cyan
Write-Host "1. Rebuild: docker build -t modelselectionchat:latest ." -ForegroundColor White
Write-Host "2. Run: docker run -p 8501:8501 --env-file .env modelselectionchat:latest" -ForegroundColor White
