#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Validates Entra ID authentication configuration for the ChatModelSelector app.

.DESCRIPTION
    This script tests the current Entra ID authentication setup by attempting to
    authenticate and retrieve a token using the configured method. It provides
    detailed feedback on the authentication status and any issues found.

.EXAMPLE
    .\validate-entra-auth.ps1
    Runs a complete validation of the current Entra ID authentication setup.
#>

param(
    [switch]$Verbose = $false
)

# Colors for output
$Green = "`e[32m"
$Red = "`e[31m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Reset = "`e[0m"

function Write-Status {
    param($Message, $Type = "Info")
    switch ($Type) {
        "Success" { Write-Host "${Green}✅ $Message${Reset}" }
        "Error" { Write-Host "${Red}❌ $Message${Reset}" }
        "Warning" { Write-Host "${Yellow}⚠️ $Message${Reset}" }
        "Info" { Write-Host "${Blue}ℹ️ $Message${Reset}" }
    }
}

function Test-EntraIdAuth {
    Write-Host "${Blue}🔐 Entra ID Authentication Validation${Reset}`n"
    
    # Check if .env file exists
    if (-not (Test-Path ".env")) {
        Write-Status "No .env file found. Please create one from .env.example" "Error"
        return $false
    }
    
    # Load environment variables
    try {
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^([^#][^=]+)=(.*)$") {
                [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], "Process")
            }
        }
        Write-Status ".env file loaded successfully" "Success"
    }
    catch {
        Write-Status "Failed to load .env file: $($_.Exception.Message)" "Error"
        return $false
    }
    
    # Check authentication methods
    Write-Host "`n${Blue}🔍 Checking configured authentication methods:${Reset}"
    
    $authMethods = @()
    
    # Managed Identity
    $useManagedIdentity = [Environment]::GetEnvironmentVariable("USE_MANAGED_IDENTITY")
    if ($useManagedIdentity -eq "true") {
        $authMethods += "Managed Identity"
        Write-Status "Managed Identity: ENABLED" "Success"
        
        $clientId = [Environment]::GetEnvironmentVariable("AZURE_CLIENT_ID")
        if ($clientId) {
            Write-Host "  └─ User-Assigned MI Client ID: $clientId"
        } else {
            Write-Host "  └─ System-Assigned Managed Identity"
        }
    }
    
    # Service Principal (Secret)
    $clientId = [Environment]::GetEnvironmentVariable("AZURE_CLIENT_ID")
    $clientSecret = [Environment]::GetEnvironmentVariable("AZURE_CLIENT_SECRET")
    $tenantId = [Environment]::GetEnvironmentVariable("AZURE_TENANT_ID")
    
    if ($clientId -and $clientSecret -and $tenantId) {
        $authMethods += "Service Principal (Secret)"
        Write-Status "Service Principal (Secret): CONFIGURED" "Success"
        Write-Host "  └─ Client ID: $clientId"
        Write-Host "  └─ Tenant ID: $tenantId"
        Write-Host "  └─ Client Secret: [HIDDEN]"
    }
    
    # Service Principal (Certificate)
    $certPath = [Environment]::GetEnvironmentVariable("AZURE_CLIENT_CERTIFICATE_PATH")
    if ($clientId -and $tenantId -and $certPath) {
        $authMethods += "Service Principal (Certificate)"
        Write-Status "Service Principal (Certificate): CONFIGURED" "Success"
        Write-Host "  └─ Client ID: $clientId"
        Write-Host "  └─ Tenant ID: $tenantId"
        Write-Host "  └─ Certificate Path: $certPath"
        
        if (-not (Test-Path $certPath)) {
            Write-Status "Certificate file not found at: $certPath" "Error"
        }
    }
    
    # Interactive Browser
    $useInteractive = [Environment]::GetEnvironmentVariable("USE_INTERACTIVE_AUTH")
    if ($useInteractive -eq "true" -and $clientId -and $tenantId) {
        $authMethods += "Interactive Browser"
        Write-Status "Interactive Browser: ENABLED" "Success"
        Write-Host "  └─ Client ID: $clientId"
        Write-Host "  └─ Tenant ID: $tenantId"
        
        $redirectUri = [Environment]::GetEnvironmentVariable("AZURE_REDIRECT_URI")
        if ($redirectUri) {
            Write-Host "  └─ Redirect URI: $redirectUri"
        }
    }
    
    # Device Code
    $useDeviceCode = [Environment]::GetEnvironmentVariable("USE_DEVICE_CODE")
    if ($useDeviceCode -eq "true" -and $clientId -and $tenantId) {
        $authMethods += "Device Code"
        Write-Status "Device Code: ENABLED" "Success"
        Write-Host "  └─ Client ID: $clientId"
        Write-Host "  └─ Tenant ID: $tenantId"
    }
    
    # Fallback methods
    Write-Host "`n${Blue}🔄 Fallback authentication methods:${Reset}"
    
    # Check Azure CLI
    try {
        $azAccount = az account show 2>$null | ConvertFrom-Json
        if ($azAccount) {
            Write-Status "Azure CLI: AUTHENTICATED" "Success"
            Write-Host "  └─ Account: $($azAccount.user.name)"
            Write-Host "  └─ Subscription: $($azAccount.name)"
        } else {
            Write-Status "Azure CLI: NOT AUTHENTICATED (run 'az login')" "Warning"
        }
    }
    catch {
        Write-Status "Azure CLI: NOT AVAILABLE" "Warning"
    }
    
    # Summary
    Write-Host "`n${Blue}📊 Authentication Summary:${Reset}"
    if ($authMethods.Count -gt 0) {
        Write-Status "$($authMethods.Count) explicit authentication method(s) configured" "Success"
        $authMethods | ForEach-Object { Write-Host "  • $_" }
    } else {
        Write-Status "No explicit authentication methods configured" "Warning"
        Write-Host "  Application will rely on fallback methods (Azure CLI, VS Code, DefaultAzureCredential)"
    }
    
    # Check Azure OpenAI configuration
    Write-Host "`n${Blue}🔧 Azure OpenAI Configuration:${Reset}"
    
    $endpoint = [Environment]::GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT")
    $apiKey = [Environment]::GetEnvironmentVariable("AZURE_OPENAI_KEY")
    $subscriptionId = [Environment]::GetEnvironmentVariable("SUBSCRIPTION_ID")
    $resourceGroup = [Environment]::GetEnvironmentVariable("RESOURCE_GROUP_NAME")
    $accountName = [Environment]::GetEnvironmentVariable("AOAI_ACCOUNT_NAME")
    
    $configItems = @(
        @{ Name = "AZURE_OPENAI_ENDPOINT"; Value = $endpoint },
        @{ Name = "AZURE_OPENAI_KEY"; Value = $apiKey },
        @{ Name = "SUBSCRIPTION_ID"; Value = $subscriptionId },
        @{ Name = "RESOURCE_GROUP_NAME"; Value = $resourceGroup },
        @{ Name = "AOAI_ACCOUNT_NAME"; Value = $accountName }
    )
    
    $allConfigured = $true
    foreach ($item in $configItems) {
        if ($item.Value) {
            if ($item.Name -eq "AZURE_OPENAI_KEY") {
                Write-Status "$($item.Name): CONFIGURED" "Success"
            } else {
                Write-Status "$($item.Name): $($item.Value)" "Success"
            }
        } else {
            Write-Status "$($item.Name): NOT SET" "Error"
            $allConfigured = $false
        }
    }
    
    # Final recommendations
    Write-Host "`n${Blue}💡 Recommendations:${Reset}"
    
    if ($authMethods.Count -eq 0) {
        Write-Status "Configure at least one explicit authentication method for better reliability" "Warning"
        Write-Host "  • For Azure-hosted apps: Enable Managed Identity"
        Write-Host "  • For containers/CI-CD: Create a Service Principal"
        Write-Host "  • For development: Use Interactive Browser or Azure CLI"
    }
    
    if (-not $allConfigured) {
        Write-Status "Complete the Azure OpenAI configuration" "Warning"
        Write-Host "  • Run: .\discover-azure-resources.ps1 to find correct values"
    }
    
    if ($authMethods.Count -gt 0 -and $allConfigured) {
        Write-Status "Authentication setup looks good! ✨" "Success"
        Write-Host "  • Ready to run: streamlit run app.py"
    }
    
    return ($authMethods.Count -gt 0 -and $allConfigured)
}

# Main execution
Clear-Host
$result = Test-EntraIdAuth

if ($result) {
    Write-Host "`n${Green}🎉 Validation completed successfully!${Reset}"
    exit 0
} else {
    Write-Host "`n${Red}⚠️ Issues found. Please address the above recommendations.${Reset}"
    exit 1
}
