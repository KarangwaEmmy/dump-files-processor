#!/usr/bin/env bash
set -euo pipefail

# One-click deploy from WSL -> C:\\dump_listener
# - copies repository files (excludes .git, venv, pyc)
# - deploys .env file from WSL to Windows
# - creates Windows `monitor.env` (Windows-specific overrides), `service.bat`
# - drops a PowerShell helper `setup_windows_env.ps1` into the target
# - invokes PowerShell to create the Windows venv and install requirements

SRC_DIR="$(pwd)"
DEST_WIN="/mnt/c/dump_listener"
DEST_DUMP="/mnt/c/Dump"

echo "Step 1/8: Deploying workspace from $SRC_DIR to $DEST_WIN"

# ensure destination exists
mkdir -p "$DEST_WIN"

echo "Step 2/8: Ensuring C:\\Dump exists"
mkdir -p "$DEST_DUMP"

echo "Step 3/8: Syncing files to $DEST_WIN (excludes .git, venv, __pycache__, logs)"
rsync -a --delete \
  --exclude '.git' \
  --exclude 'venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude 'logs' \
  "$SRC_DIR"/ "$DEST_WIN"/

echo "Step 4/8: Deploying .env file from WSL to Windows"
if [ -f "$SRC_DIR/../.env" ]; then
  cp "$SRC_DIR/../.env" "$DEST_WIN/.env"
  echo "  ✓ .env deployed to $DEST_WIN/.env"
else
  echo "  ⚠ Warning: .env not found in $SRC_DIR/.."
fi

echo "Step 5/8: Creating Windows environment file (monitor.env)"
cat > "$DEST_WIN/monitor.env" <<'ENV'
# Windows environment for dump_listener
DUMP_DIR=C:\\Dump
LOG_DIR=C:\\dump_listener\\logs
ENV

echo "Step 6/8: Creating service.bat"
cat > "$DEST_WIN/service.bat" <<'BAT'
@echo off
cd C:\\dump_listener
C:\\dump_listener\\venv\\Scripts\\python.exe main.py
BAT

echo "Step 7/8: Dropping PowerShell helper: setup_windows_env.ps1"
cat > "$DEST_WIN/setup_windows_env.ps1" <<'PS'
# setup_windows_env.ps1
# Creates a venv in C:\\dump_listener, ensures C:\\Dump exists and installs requirements
Set-StrictMode -Version Latest
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
Push-Location 'C:\\dump_listener'

if (-not (Test-Path -Path 'C:\\Dump')) {
  Write-Host 'Creating C:\\Dump'
  New-Item -Path 'C:\\Dump' -ItemType Directory -Force | Out-Null
}

if (-not (Test-Path -Path '.\\venv')) {
  Write-Host 'Creating virtual environment in C:\\dump_listener\\venv'
  python -m venv venv
}

Write-Host 'Upgrading pip and installing requirements'
& .\\venv\\Scripts\\python.exe -m pip install --upgrade pip
if (Test-Path -Path '.\\requirements.txt') {
  & .\\venv\\Scripts\\python.exe -m pip install -r .\\requirements.txt
}

Write-Host 'Setup complete.'
Pop-Location
PS

echo "Step 8/8: Invoking PowerShell to finalize Windows venv and packages..."
# Use powershell.exe from WSL to run the script on Windows
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\\dump_listener\\setup_windows_env.ps1" || true

echo "Deployment finished."
echo "- .env file: C:\\dump_listener\\.env (from WSL)"
echo "- Windows env file: C:\\dump_listener\\monitor.env (Windows-specific overrides)"
echo "- service batch: C:\\dump_listener\\service.bat"
echo "- Dump folder: C:\\Dump"
echo "To run as service: use NSSM or Task Scheduler on Windows."

exit 0
