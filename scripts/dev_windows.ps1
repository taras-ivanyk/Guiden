# Guiden — start both servers (Windows PowerShell)
# Usage: .\scripts\dev_windows.ps1
#
# If you get an execution policy error, run once as admin:
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
Set-Location $ROOT

# ── Checks ───────────────────────────────────────────────────────
if (-not (Test-Path "venv\Scripts\activate.ps1")) {
    Write-Host "x No venv found. Run: python -m venv venv && pip install -r requirements.txt"
    exit 1
}
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "x No node_modules. Run: cd frontend && npm install"
    exit 1
}
if (-not (Test-Path ".env")) {
    Write-Host "x No .env file. Copy .env.example and fill in your keys."
    exit 1
}

# ── Backend ──────────────────────────────────────────────────────
$uvicorn = Resolve-Path "venv\Scripts\uvicorn.exe"
$backend = Start-Process -PassThru -NoNewWindow `
    -FilePath $uvicorn `
    -ArgumentList "backend.main:app", "--reload", "--port", "8000"
Write-Host "v Backend  -> http://127.0.0.1:8000  (PID $($backend.Id))"

# ── Cleanup on exit ──────────────────────────────────────────────
function Stop-All {
    Write-Host "`n<- Shutting down..."
    Stop-Process -Id $backend.Id -ErrorAction SilentlyContinue
}

# ── Frontend ─────────────────────────────────────────────────────
try { nvm use 18 2>$null } catch { }

Write-Host "v Frontend -> http://localhost:5173"
Write-Host ""
Write-Host "  Press Ctrl+C to stop everything."
Write-Host ""

try {
    Set-Location frontend
    npm run dev
} finally {
    Stop-All
}
