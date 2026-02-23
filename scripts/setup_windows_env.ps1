<#
Helper PowerShell script template (also deployed to C:\dump_listener by the shell deployer).
This file can be run on Windows to create the venv and install requirements.
#>

Set-StrictMode -Version Latest
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
Push-Location 'C:\dump_listener'

if (-not (Test-Path -Path 'C:\Dump')) {
    Write-Host 'Creating C:\Dump'
    New-Item -Path 'C:\Dump' -ItemType Directory -Force | Out-Null
}

if (-not (Test-Path -Path '.\venv')) {
    Write-Host 'Creating virtual environment in C:\dump_listener\venv'
    python -m venv venv
}

Write-Host 'Upgrading pip and installing requirements'
& .\venv\Scripts\python.exe -m pip install --upgrade pip
if (Test-Path -Path '.\requirements.txt') {
    & .\venv\Scripts\python.exe -m pip install -r .\requirements.txt
}

Write-Host 'Setup complete.'
Pop-Location
