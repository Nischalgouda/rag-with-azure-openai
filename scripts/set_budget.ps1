<#
.SYNOPSIS
  Create (or update) a monthly cost budget on the current Azure subscription with email alerts.

.DESCRIPTION
  Alerts at 50%, 80% and 100% of ACTUAL spend, and when the FORECAST says you will reach 100%.
  The amount is in your BILLING currency (the Azure portal showed INR for this account), so 1000 means
  1,000 rupees, about 11 USD. A budget only sends email: it does NOT stop spending. The real brakes are the
  app's daily token budget, the kill switch (DEMO_ENABLED=false) and, on a free-credit account, the credit itself.

.EXAMPLE
  .\scripts\set_budget.ps1 -Email you@example.com
  .\scripts\set_budget.ps1 -Email you@example.com -Amount 500 -Name my-budget
#>
param(
  [Parameter(Mandatory = $true)][string]$Email,
  [double]$Amount = 1000,
  [string]$Name = "rag-demo-monthly",
  [string]$StartDate = (Get-Date -Day 1).ToString("yyyy-MM-01"),
  [string]$EndDate = (Get-Date -Day 1).AddYears(1).ToString("yyyy-MM-01")
)

$ErrorActionPreference = "Stop"
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
  $azdir = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"
  if (Test-Path $azdir) { $env:Path += ";$azdir" } else { throw "Azure CLI not found." }
}

$sub = az account show --query id --output tsv
if ($LASTEXITCODE -ne 0) { throw "Not signed in. Run 'az login' first." }
az provider register --namespace Microsoft.Consumption --wait | Out-Null

function Note($type, $pct) {
  @{ enabled = $true; operator = "GreaterThan"; threshold = $pct; thresholdType = $type; contactEmails = @($Email) }
}
$body = @{ properties = @{
  category = "Cost"; amount = $Amount; timeGrain = "Monthly"
  timePeriod = @{ startDate = "${StartDate}T00:00:00Z"; endDate = "${EndDate}T00:00:00Z" }
  notifications = @{
    Actual_50 = (Note "Actual" 50); Actual_80 = (Note "Actual" 80)
    Actual_100 = (Note "Actual" 100); Forecast_100 = (Note "Forecasted" 100)
  }
} } | ConvertTo-Json -Depth 8

$file = Join-Path $env:TEMP "budget.json"
[System.IO.File]::WriteAllText($file, $body, (New-Object System.Text.UTF8Encoding($false)))
$url = "https://management.azure.com/subscriptions/$sub/providers/Microsoft.Consumption/budgets/${Name}?api-version=2023-05-01"
az rest --method put --url $url --body "@$file" --output none
if ($LASTEXITCODE -ne 0) { throw "Budget creation failed." }
Write-Host "Budget '$Name' set: $Amount per month, alerts to $Email (50%, 80%, 100% actual and 100% forecast)." -ForegroundColor Green
