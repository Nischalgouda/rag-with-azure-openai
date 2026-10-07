<#
.SYNOPSIS
  Deploy the hosted demo to Azure Container Apps from a published image.

.DESCRIPTION
  Reads your local .env so you never paste keys into a terminal, stores the two API keys as
  Container Apps SECRETS (not plain environment variables), and creates a single-replica app with
  public HTTPS ingress. Run with -DryRun first to see exactly what would be executed (keys masked).

  STATUS: written against the Azure CLI documentation but NOT yet run against a live subscription.
  Read docs/DEPLOY.md before the first run.

.EXAMPLE
  .\scripts\deploy_azure.ps1 -DryRun
  .\scripts\deploy_azure.ps1 -Image ghcr.io/nischalgouda/rag-with-azure-openai:0.2.0
#>
param(
  [string]$ResourceGroup = "rg-rag-demo",
  [string]$Location = "eastus",
  [string]$AppName = "rag-xray",
  [string]$EnvironmentName = "rag-xray-env",
  [string]$Image = "ghcr.io/nischalgouda/rag-with-azure-openai:latest",
  [string]$EnvFile = ".env",
  # One replica on purpose: rate limits and daily counters live in this process's memory/disk.
  [int]$MinReplicas = 1,
  [int]$MaxReplicas = 1,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Read-DotEnv([string]$Path) {
  if (-not (Test-Path $Path)) { throw "Env file '$Path' not found. Run from the repo root." }
  $map = @{}
  foreach ($line in Get-Content $Path) {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$') { $map[$Matches[1]] = $Matches[2].Trim('"') }
  }
  return $map
}

function Require([hashtable]$Map, [string]$Key) {
  if (-not $Map.ContainsKey($Key) -or [string]::IsNullOrWhiteSpace($Map[$Key])) { throw "Missing $Key in $EnvFile" }
  return $Map[$Key]
}

$cfg = Read-DotEnv $EnvFile
$aoaiEndpoint = Require $cfg "AZURE_OPENAI_ENDPOINT"
$aoaiKey      = Require $cfg "AZURE_OPENAI_API_KEY"
$searchEnd    = Require $cfg "SEARCH_ENDPOINT"
$searchKey    = Require $cfg "SEARCH_API_KEY"

$envVars = @(
  "DEMO_MODE=true",
  "VECTOR_STORE=azure_search",
  "EMBEDDING_PROVIDER=azure",
  "LLM_PROVIDER=azure",
  "AZURE_OPENAI_ENDPOINT=$aoaiEndpoint",
  "AZURE_OPENAI_API_KEY=secretref:aoai-key",
  "AZURE_OPENAI_CHAT_DEPLOYMENT=$(if ($cfg.ContainsKey('AZURE_OPENAI_CHAT_DEPLOYMENT')) { $cfg['AZURE_OPENAI_CHAT_DEPLOYMENT'] } else { 'gpt-4.1-mini' })",
  "AZURE_OPENAI_EMBEDDING_DEPLOYMENT=$(if ($cfg.ContainsKey('AZURE_OPENAI_EMBEDDING_DEPLOYMENT')) { $cfg['AZURE_OPENAI_EMBEDDING_DEPLOYMENT'] } else { 'text-embedding-3-small' })",
  "SEARCH_ENDPOINT=$searchEnd",
  "SEARCH_API_KEY=secretref:search-key",
  "SEARCH_INDEX_NAME=$(if ($cfg.ContainsKey('SEARCH_INDEX_NAME')) { $cfg['SEARCH_INDEX_NAME'] } else { 'rag-chunks' })",
  "MIN_SCORE=$(if ($cfg.ContainsKey('MIN_SCORE')) { $cfg['MIN_SCORE'] } else { '0.23' })"
)

function Invoke-Az([string[]]$AzArgs, [string[]]$Secrets = @()) {
  $shown = ($AzArgs -join " ")
  foreach ($s in $Secrets) { if ($s) { $shown = $shown.Replace($s, "***") } }
  Write-Host "> az $shown" -ForegroundColor Cyan
  if ($DryRun) { return }
  & az @AzArgs
  if ($LASTEXITCODE -ne 0) { throw "az command failed (exit $LASTEXITCODE)" }
}

if (-not $DryRun) {
  if (-not (Get-Command az -ErrorAction SilentlyContinue)) { throw "Azure CLI not found. Install it, then run 'az login'." }
  az account show --output none 2>$null
  if ($LASTEXITCODE -ne 0) { throw "Not signed in. Run 'az login' first." }
}

Invoke-Az @("extension", "add", "--name", "containerapp", "--upgrade", "--only-show-errors")
Invoke-Az @("provider", "register", "--namespace", "Microsoft.App", "--wait")
Invoke-Az @("provider", "register", "--namespace", "Microsoft.OperationalInsights", "--wait")

Invoke-Az @("containerapp", "env", "create", "--name", $EnvironmentName, "--resource-group", $ResourceGroup, "--location", $Location)

Invoke-Az -Secrets @($aoaiKey, $searchKey) -AzArgs (@(
  "containerapp", "create",
  "--name", $AppName,
  "--resource-group", $ResourceGroup,
  "--environment", $EnvironmentName,
  "--image", $Image,
  "--target-port", "8000",
  "--ingress", "external",
  "--min-replicas", "$MinReplicas",
  "--max-replicas", "$MaxReplicas",
  "--cpu", "0.25", "--memory", "0.5Gi",
  "--secrets", "aoai-key=$aoaiKey", "search-key=$searchKey",
  "--env-vars") + $envVars)

if (-not $DryRun) {
  $fqdn = az containerapp show --name $AppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn --output tsv
  Write-Host "`nDeployed: https://$fqdn" -ForegroundColor Green
  Write-Host "Next: create an admin key (docs/DEPLOY.md), then set a budget alert." -ForegroundColor Green
}
