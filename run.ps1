# One-command launcher: works from ANY folder.
#   powershell -ExecutionPolicy Bypass -File <path-to-project>\run.ps1
# Finds/creates a Python 3.12 environment OUTSIDE the project (so cleanups can't delete it), installs
# requirements if needed, makes .env from .env.example if missing, then starts Streamlit.
param([switch]$NoRun)

$ErrorActionPreference = "Stop"
$proj = $PSScriptRoot
Set-Location $proj
$venv = Join-Path $env:USERPROFILE "venvs\custfeedbackspy"
$py = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $py)) {
    Write-Host "Creating Python 3.12 environment at $venv ..."
    New-Item -ItemType Directory -Force (Split-Path $venv) | Out-Null
    py -3.12 -m venv $venv
    if (-not (Test-Path $py)) { throw "Python 3.12 not found. Install it from python.org, then run this again." }
}

& $py -c "import streamlit, langchain_core, pandas" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing requirements (first run only) ..."
    & $py -m pip install -q -r (Join-Path $proj "requirements.txt")
}

if (-not (Test-Path (Join-Path $proj ".env"))) {
    Copy-Item (Join-Path $proj ".env.example") (Join-Path $proj ".env")
    Write-Host "Created .env from .env.example (mock mode). Add your API key there for a real LLM."
}

Write-Host "Project : $proj"
Write-Host "Python  : $py"
if ($NoRun) { Write-Host "OK (NoRun)"; exit 0 }
& $py -m streamlit run (Join-Path $proj "app.py")
