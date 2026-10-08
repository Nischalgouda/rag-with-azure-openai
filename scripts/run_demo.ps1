<#
.SYNOPSIS
  Start RAG X-ray locally exactly as it will run in production: UI + API from one server, against your
  live Azure resources (from .env). Use this to rehearse and to record the demo video.

.EXAMPLE
  .\scripts\run_demo.ps1            # builds the UI if needed, warms the model, opens the browser
  .\scripts\run_demo.ps1 -Rebuild   # force a fresh UI build after frontend changes
  .\scripts\run_demo.ps1 -NoBrowser

.NOTES
  Runs with DEMO_MODE off, so the 15-questions-a-day visitor limit does not interrupt a recording.
  One warm-up question is sent first so the first on-camera question is not the slow one.
#>
param(
  [int]$Port = 8010,
  [switch]$Rebuild,
  [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".\.venv\Scripts\python.exe")) { throw "No .venv found. Follow 'Quick start' in the README first." }
if (-not (Test-Path ".\.env")) { throw "No .env found. Copy .env.example to .env and fill it in." }

if ($Rebuild -or -not (Test-Path ".\frontend\dist\index.html")) {
  Write-Host "Building the UI..." -ForegroundColor Cyan
  Push-Location frontend
  if (-not (Test-Path "node_modules")) { npm install }
  npm run build
  if ($LASTEXITCODE -ne 0) { Pop-Location; throw "Frontend build failed" }
  Pop-Location
}

$env:STATIC_DIR = (Resolve-Path ".\frontend\dist").Path
$env:DEMO_MODE = "false"

# Background job: wait for the server, warm it up, then open the browser.
$helper = Start-Job -ArgumentList $Port, [bool]$NoBrowser -ScriptBlock {
  param($p, $skipBrowser)
  $up = $false
  for ($i = 0; $i -lt 40 -and -not $up; $i++) {
    try { Invoke-WebRequest "http://localhost:$p/api/health" -UseBasicParsing -TimeoutSec 2 | Out-Null; $up = $true }
    catch { Start-Sleep -Seconds 1 }
  }
  if ($up) {
    try {
      Invoke-RestMethod -Method Post -Uri "http://localhost:$p/api/ask" -ContentType "application/json" `
        -Body '{"question":"How big is the free tier of Azure AI Search?","trace":true}' | Out-Null
    } catch { }
    if (-not $skipBrowser) { Start-Process "http://localhost:$p" }
  }
}

Write-Host "RAG X-ray on http://localhost:$Port  (Ctrl+C to stop)" -ForegroundColor Green
try {
  & ".\.venv\Scripts\python.exe" -m uvicorn app.server:app --port $Port
}
finally {
  Stop-Job $helper -ErrorAction SilentlyContinue
  Remove-Job $helper -Force -ErrorAction SilentlyContinue
}
