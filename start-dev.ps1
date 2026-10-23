$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Virtual environment not found at $python"
}

$backendListener = Get-NetTCPConnection -LocalPort 8011 -State Listen -ErrorAction SilentlyContinue
if (-not $backendListener) {
    Start-Process -FilePath $python -ArgumentList @(
        "-m", "uvicorn", "app.main:app", "--app-dir", "backend",
        "--host", "127.0.0.1", "--port", "8011"
    ) -WorkingDirectory $root -WindowStyle Hidden
}

Set-Location (Join-Path $root "frontend")
$env:VITE_API_TARGET = "http://127.0.0.1:8011"
npm run dev:frontend
