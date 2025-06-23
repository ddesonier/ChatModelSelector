# Test Entra ID Authentication Methods
# This script helps you test different Entra ID authentication methods

param(
    [string]$EnvFile = ".env",
    [switch]$TestAll = $false
)

Write-Host "Testing Entra ID Authentication Methods..." -ForegroundColor Green
Write-Host ""

# Load environment variables
if (Test-Path $EnvFile) {
    $envContent = Get-Content $EnvFile
    foreach ($line in $envContent) {
        if ($line -and $line.Trim() -and -not $line.StartsWith("#")) {
            $parts = $line.Split("=", 2)
            if ($parts.Count -eq 2) {
                $name = $parts[0].Trim()
                $value = $parts[1].Trim()
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
    }
    Write-Host "Environment variables loaded from $EnvFile" -ForegroundColor Blue
} else {
    Write-Host "WARNING: $EnvFile not found. Using system environment variables." -ForegroundColor Yellow
}

Write-Host ""

# Test authentication methods
$methods = @()

# Method 1: Managed Identity
$useManagedIdentity = $env:USE_MANAGED_IDENTITY -eq 'true'
if ($useManagedIdentity) {
    $methods += @{
        Name = "Managed Identity"
        Icon = "🎯"
        Status = "CONFIGURED"
        Description = "Using Azure Managed Identity"
        Details = if ($env:AZURE_CLIENT_ID) { "User-Assigned MI: $($env:AZURE_CLIENT_ID)" } else { "System-Assigned MI" }
    }
} else {
    $methods += @{
        Name = "Managed Identity"
        Icon = "🎯"
        Status = "DISABLED"
        Description = "Set USE_MANAGED_IDENTITY=true to enable"
        Details = ""
    }
}

# Method 2: Service Principal (Secret)
if ($env:AZURE_CLIENT_ID -and $env:AZURE_CLIENT_SECRET -and $env:AZURE_TENANT_ID) {
    $methods += @{
        Name = "Service Principal (Secret)"
        Icon = "🔑"
        Status = "CONFIGURED"
        Description = "Client Secret authentication"
        Details = "Client ID: $($env:AZURE_CLIENT_ID)"
    }
} else {
    $methods += @{
        Name = "Service Principal (Secret)"
        Icon = "🔑"
        Status = "NOT CONFIGURED"
        Description = "Missing AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, or AZURE_TENANT_ID"
        Details = ""
    }
}

# Method 3: Service Principal (Certificate)
if ($env:AZURE_CLIENT_ID -and $env:AZURE_CLIENT_CERTIFICATE_PATH -and $env:AZURE_TENANT_ID) {
    $certExists = Test-Path $env:AZURE_CLIENT_CERTIFICATE_PATH
    $methods += @{
        Name = "Service Principal (Certificate)"
        Icon = "📜"
        Status = if ($certExists) { "CONFIGURED" } else { "CERT NOT FOUND" }
        Description = "Certificate-based authentication"
        Details = "Certificate: $($env:AZURE_CLIENT_CERTIFICATE_PATH)"
    }
} else {
    $methods += @{
        Name = "Service Principal (Certificate)"
        Icon = "📜"
        Status = "NOT CONFIGURED"
        Description = "Missing AZURE_CLIENT_ID, AZURE_CLIENT_CERTIFICATE_PATH, or AZURE_TENANT_ID"
        Details = ""
    }
}

# Method 4: Interactive Browser
$useInteractive = $env:USE_INTERACTIVE_AUTH -eq 'true'
if ($useInteractive -and $env:AZURE_CLIENT_ID -and $env:AZURE_TENANT_ID) {
    $methods += @{
        Name = "Interactive Browser"
        Icon = "🌐"
        Status = "ENABLED"
        Description = "Browser-based authentication"
        Details = "App Registration: $($env:AZURE_CLIENT_ID)"
    }
} else {
    $methods += @{
        Name = "Interactive Browser"
        Icon = "🌐"
        Status = "DISABLED"
        Description = "Set USE_INTERACTIVE_AUTH=true and provide AZURE_CLIENT_ID, AZURE_TENANT_ID"
        Details = ""
    }
}

# Method 5: Device Code
$useDeviceCode = $env:USE_DEVICE_CODE -eq 'true'
if ($useDeviceCode -and $env:AZURE_CLIENT_ID -and $env:AZURE_TENANT_ID) {
    $methods += @{
        Name = "Device Code"
        Icon = "📱"
        Status = "ENABLED"
        Description = "Device code flow authentication"
        Details = "App Registration: $($env:AZURE_CLIENT_ID)"
    }
} else {
    $methods += @{
        Name = "Device Code"
        Icon = "📱"
        Status = "DISABLED"
        Description = "Set USE_DEVICE_CODE=true and provide AZURE_CLIENT_ID, AZURE_TENANT_ID"
        Details = ""
    }
}

# Method 6: Azure CLI
try {
    $azAccount = az account show --output json 2>$null | ConvertFrom-Json
    if ($azAccount) {
        $methods += @{
            Name = "Azure CLI"
            Icon = "🖥️"
            Status = "AVAILABLE"
            Description = "Azure CLI authentication"
            Details = "Logged in as: $($azAccount.user.name)"
        }
    } else {
        $methods += @{
            Name = "Azure CLI"
            Icon = "🖥️"
            Status = "NOT LOGGED IN"
            Description = "Run 'az login' to enable"
            Details = ""
        }
    }
} catch {
    $methods += @{
        Name = "Azure CLI"
        Icon = "🖥️"
        Status = "NOT INSTALLED"
        Description = "Azure CLI not found"
        Details = ""
    }
}

# Display results
Write-Host "Authentication Methods Status:" -ForegroundColor Yellow
Write-Host "=" * 60

foreach ($method in $methods) {
    $color = switch ($method.Status) {
        "CONFIGURED" { "Green" }
        "ENABLED" { "Green" }
        "AVAILABLE" { "Green" }
        "DISABLED" { "Yellow" }
        "NOT CONFIGURED" { "Red" }
        "NOT LOGGED IN" { "Yellow" }
        "NOT INSTALLED" { "Red" }
        "CERT NOT FOUND" { "Red" }
        default { "White" }
    }
    
    Write-Host "$($method.Icon) $($method.Name): " -NoNewline -ForegroundColor White
    Write-Host $method.Status -ForegroundColor $color
    Write-Host "   $($method.Description)" -ForegroundColor Gray
    if ($method.Details) {
        Write-Host "   $($method.Details)" -ForegroundColor DarkGray
    }
    Write-Host ""
}

# Recommendations
Write-Host "Recommendations:" -ForegroundColor Cyan
$configuredMethods = ($methods | Where-Object { $_.Status -in @("CONFIGURED", "ENABLED", "AVAILABLE") }).Count

if ($configuredMethods -eq 0) {
    Write-Host "❌ No authentication methods are properly configured!" -ForegroundColor Red
    Write-Host "   Recommended: Create a Service Principal for reliable authentication" -ForegroundColor Yellow
    Write-Host "   Run: .\create-service-principal.ps1 -ServicePrincipalName 'ModelSelectorApp'" -ForegroundColor Cyan
} elseif ($configuredMethods -eq 1 -and ($methods | Where-Object { $_.Name -eq "Azure CLI" -and $_.Status -eq "AVAILABLE" })) {
    Write-Host "⚠️ Only Azure CLI authentication is available" -ForegroundColor Yellow
    Write-Host "   This works for local development but won't work in containers" -ForegroundColor Yellow
    Write-Host "   For production: Configure Service Principal or Managed Identity" -ForegroundColor Cyan
} else {
    Write-Host "✅ Multiple authentication methods available - good for reliability!" -ForegroundColor Green
    Write-Host "   The app will try methods in priority order" -ForegroundColor White
}

Write-Host ""
Write-Host "To test the app with current configuration:" -ForegroundColor Green
Write-Host "streamlit run app.py" -ForegroundColor Cyan
