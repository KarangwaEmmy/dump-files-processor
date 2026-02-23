<#
Small wrapper to run the listener. Edit `$Env:DUMP_DIR` if needed.
Run this from an elevated prompt or the scheduled task action.
#>

param(
    [string]$PythonPath = "python"
)

Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Definition)

# Default dump dir; change to your preferred path
$Env:DUMP_DIR = "$Env:USERPROFILE\\Dump"

Write-Host "Starting dump listener with DUMP_DIR=$Env:DUMP_DIR"
& $PythonPath "main.py"
