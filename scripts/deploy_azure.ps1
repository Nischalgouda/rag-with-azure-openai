<#
.SYNOPSIS
  Deploy the hosted demo to Azure Container Apps.

.DESCRIPTION
  Two ways to get the container image to Azure:
    -Registry acr   (default) creates an Azure Container Registry (Basic tier, a few dollars/month), builds the
                    image locally with Docker and pushes it. No GitHub package needed. (`-Build tasks` builds in
                    Azure instead, but Azure blocks that on free-credit subscriptions.)
    -Registry ghcr  uses an image already published by CI to GitHub Container Registry (see docs/DEPLOY.md).

  Keys are read from your local .env (never typed into a terminal) and stored as Container Apps SECRETS.
  Run with -DryRun first to see exactly what would be executed (secrets masked).

.EXAMPLE
  .\scripts\deploy_azure.ps1 -DryRun
  .\scripts\deploy_azure.ps1
  .\scripts\deploy_azure.ps1 -Registry ghcr -Image ghcr.io/nischalgouda/rag-with-azure-openai:0.2.0
#>
param(
  [string]$ResourceGroup = "rg-rag-demo",
  # Where the app environment runs. Azure sometimes has no capacity in a region (we hit AKSCapacityHeavyUsage in
  # eastus); pick another with -Location. The registry can live elsewhere, the app pulls over the network.
  [string]$Location = "centralus",
  [string]$RegistryLocation = "eastus",
  [string]$AppName = "rag-xray",
  [string]$EnvironmentName = "rag-xray-env",
  [ValidateSet("acr", "ghcr")][string]$Registry = "acr",
  # local: build with Docker here and push to ACR (works everywhere). tasks: `az acr build` in Azure,
  # which Azure blocks on free-credit subscriptions.
  [ValidateSet("local", "tasks")][string]$Build = "local",
  [string]$Tag = "0.2.0",
  [string]$Image = "ghcr.io/nischalgouda/rag-with-azure-openai:latest",
  [string]$EnvFile = ".env",
  # One replica on purpose: rate limits and daily counters live in this process's memory/disk.
  [int]$MinReplicas = 1,
  [int]$MaxReplicas = 1,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

# A freshly installed Azure CLI may not be on PATH in this shell yet.
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
  $azdir = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"
  if (Test-Path $azdir) { $env:Path += ";$azdir" }
}

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

function Get-Setting([hashtable]$Map, [string]$Key, [string]$Default) {
  if ($Map.ContainsKey($Key) -and -not [string]::IsNullOrWhiteSpace($Map[$Key])) { return $Map[$Key] }
  return $Default
}

$script:Secrets = @()

function Invoke-Az([string[]]$AzArgs, [switch]$Capture) {
  $shown = ($AzArgs -join " ")
  foreach ($s in $script:Secrets) { if ($s) { $shown = $shown.Replace($s, "***") } }
  Write-Host "> az $shown" -ForegroundColor Cyan
  if ($DryRun) { if ($Capture) { return "<dry-run>" } else { return } }
  if ($Capture) {
    $out = & az @AzArgs
    if ($LASTEXITCODE -ne 0) { throw "az command failed (exit $LASTEXITCODE)" }
    return ($out | Out-String).Trim()
  }
  & az @AzArgs
  if ($LASTEXITCODE -ne 0) { throw "az command failed (exit $LASTEXITCODE)" }
}

$cfg = Read-DotEnv $EnvFile
$aoaiEndpoint = Require $cfg "AZURE_OPENAI_ENDPOINT"
$aoaiKey      = Require $cfg "AZURE_OPENAI_API_KEY"
$searchEnd    = Require $cfg "SEARCH_ENDPOINT"
$searchKey    = Require $cfg "SEARCH_API_KEY"
$script:Secrets = @($aoaiKey, $searchKey)

if (-not $DryRun) {
  if (-not (Get-Command az -ErrorAction SilentlyContinue)) { throw "Azure CLI not found. Install it, then run 'az login'." }
  az account show --output none 2>$null
  if ($LASTEXITCODE -ne 0) { throw "Not signed in. Run 'az login' first." }
}

Invoke-Az @("extension", "add", "--name", "containerapp", "--upgrade", "--only-show-errors")
foreach ($ns in "Microsoft.App", "Microsoft.OperationalInsights", "Microsoft.ContainerRegistry") {
  Invoke-Az @("provider", "register", "--namespace", $ns, "--wait")
}

# ---- image -------------------------------------------------------------------------------------------
$registryArgs = @()
if ($Registry -eq "acr") {
  $subId = Invoke-Az @("account", "show", "--query", "id", "--output", "tsv") -Capture
  # ACR names are global and alphanumeric: derive a stable suffix from the subscription id.
  $sha = [System.Security.Cryptography.SHA1]::Create()
  $suffix = ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($subId))) -replace "-", "").Substring(0, 6).ToLower()
  $acr = "ragxray$suffix"
  $Image = "$acr.azurecr.io/rag-xray:$Tag"

  Invoke-Az @("acr", "create", "--name", $acr, "--resource-group", $ResourceGroup, "--location", $RegistryLocation, "--sku", "Basic", "--admin-enabled", "true")
  if ($Build -eq "tasks") {
    # Build in Azure from this folder (.dockerignore applies). NOT available on free-credit subscriptions:
    # Azure rejects it with TasksOperationsNotAllowed.
    Invoke-Az @("acr", "build", "--registry", $acr, "--image", "rag-xray:$Tag", ".")
  } else {
    # Default: build the same multi-stage Dockerfile locally and push it. Needs Docker running.
    Invoke-Az @("acr", "login", "--name", $acr)
    Write-Host "> docker build -t $Image ." -ForegroundColor Cyan
    Write-Host "> docker push $Image" -ForegroundColor Cyan
    if (-not $DryRun) {
      if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw "Docker not found. Install Docker Desktop or use -Build tasks." }
      docker build -t $Image .
      if ($LASTEXITCODE -ne 0) { throw "docker build failed (exit $LASTEXITCODE)" }
      docker push $Image
      if ($LASTEXITCODE -ne 0) { throw "docker push failed (exit $LASTEXITCODE)" }
    }
  }
  $acrUser = Invoke-Az @("acr", "credential", "show", "--name", $acr, "--query", "username", "--output", "tsv") -Capture
  $acrPass = Invoke-Az @("acr", "credential", "show", "--name", $acr, "--query", "passwords[0].value", "--output", "tsv") -Capture
  $script:Secrets += $acrPass
  $registryArgs = @("--registry-server", "$acr.azurecr.io", "--registry-username", $acrUser, "--registry-password", $acrPass)
}

# ---- app ---------------------------------------------------------------------------------------------
$envVars = @(
  "DEMO_MODE=true",
  "VECTOR_STORE=azure_search",
  "EMBEDDING_PROVIDER=azure",
  "LLM_PROVIDER=azure",
  "AZURE_OPENAI_ENDPOINT=$aoaiEndpoint",
  "AZURE_OPENAI_API_KEY=secretref:aoai-key",
  "AZURE_OPENAI_CHAT_DEPLOYMENT=$(Get-Setting $cfg 'AZURE_OPENAI_CHAT_DEPLOYMENT' 'gpt-4.1-mini')",
  "AZURE_OPENAI_EMBEDDING_DEPLOYMENT=$(Get-Setting $cfg 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT' 'text-embedding-3-small')",
  "SEARCH_ENDPOINT=$searchEnd",
  "SEARCH_API_KEY=secretref:search-key",
  "SEARCH_INDEX_NAME=$(Get-Setting $cfg 'SEARCH_INDEX_NAME' 'rag-chunks')",
  "MIN_SCORE=$(Get-Setting $cfg 'MIN_SCORE' '0.23')"
)

# The environment takes a few minutes to provision. `--no-wait` avoids holding one long polling connection (which can
# be reset by the network: we hit ConnectionResetError once); we poll gently instead and tolerate transient errors.
# The containerapp extension prints a harmless WARNING to stderr on every call. Under $ErrorActionPreference = "Stop"
# PowerShell 5.1 turns that into a terminating error, so quiet queries run with "Continue" and we judge success by the
# exit code only.
function Invoke-AzQuiet([string[]]$AzArgs) {
  $ErrorActionPreference = "Continue"
  $out = & az @AzArgs 2>$null
  return [pscustomobject]@{ Code = $LASTEXITCODE; Out = (($out | Out-String).Trim()) }
}

function Get-EnvState {
  $r = Invoke-AzQuiet @("containerapp", "env", "show", "--name", $EnvironmentName, "--resource-group", $ResourceGroup, "--query", "properties.provisioningState", "--output", "tsv")
  if ($r.Code -ne 0) { return "" }
  return $r.Out
}

if ($DryRun) {
  Invoke-Az @("containerapp", "env", "create", "--name", $EnvironmentName, "--resource-group", $ResourceGroup, "--location", $Location, "--no-wait")
} else {
  $state = Get-EnvState
  if (-not $state) {
    Invoke-Az @("containerapp", "env", "create", "--name", $EnvironmentName, "--resource-group", $ResourceGroup, "--location", $Location, "--no-wait")
    $state = "Waiting"
  } else {
    Write-Host "Environment '$EnvironmentName' already exists (state: $state); reusing it." -ForegroundColor Yellow
  }
  for ($i = 0; $i -lt 80 -and $state -ne "Succeeded"; $i++) {
    if ($state -in @("Failed", "Canceled")) { throw "Environment provisioning ended in state '$state'. Delete it and retry, or pick another -Location." }
    Write-Host "  waiting for the environment (state: $(if ($state) { $state } else { 'unknown, retrying' }))..."
    Start-Sleep -Seconds 15
    $state = Get-EnvState   # a transient network error returns "" and we simply try again
  }
  if ($state -ne "Succeeded") { throw "Timed out waiting for the environment to be ready." }
  Write-Host "Environment ready." -ForegroundColor Green
}

$appExists = $false
if (-not $DryRun) {
  $appExists = ((Invoke-AzQuiet @("containerapp", "show", "--name", $AppName, "--resource-group", $ResourceGroup, "--query", "name", "--output", "tsv")).Code -eq 0)
}

if ($appExists) {
  # Re-run safety: roll the existing app to the new image and settings instead of failing on "already exists".
  Write-Host "App '$AppName' already exists; updating it." -ForegroundColor Yellow
  Invoke-Az @("containerapp", "secret", "set", "--name", $AppName, "--resource-group", $ResourceGroup, "--secrets", "aoai-key=$aoaiKey", "search-key=$searchKey")
  Invoke-Az -AzArgs (@("containerapp", "update", "--name", $AppName, "--resource-group", $ResourceGroup, "--image", $Image, "--set-env-vars") + $envVars)
} else {
Invoke-Az -AzArgs (@(
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
  "--secrets", "aoai-key=$aoaiKey", "search-key=$searchKey") + $registryArgs + @("--env-vars") + $envVars)
}

if (-not $DryRun) {
  $fqdn = Invoke-Az @("containerapp", "show", "--name", $AppName, "--resource-group", $ResourceGroup, "--query", "properties.configuration.ingress.fqdn", "--output", "tsv") -Capture
  Write-Host "`nDeployed: https://$fqdn" -ForegroundColor Green
  Write-Host "Next: create an admin key (docs/DEPLOY.md) and set a budget alert." -ForegroundColor Green
}
