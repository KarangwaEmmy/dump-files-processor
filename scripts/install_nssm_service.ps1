<#
Install and start the DumpListener service using NSSM.
Run this file in an elevated PowerShell (Run as Administrator).
#>

# Check for Administrator
If (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script must be run as Administrator. Right-click and 'Run as Administrator'."
    exit 1
}

$nssm = 'C:\Program Files\nssm\win64\nssm.exe'
$serviceName = 'DumpListener'
$serviceBat = 'C:\dump_listener\service.bat'
$stdout = 'C:\dump_listener\logs\service.log'
$stderr = 'C:\dump_listener\logs\service_error.log'

Write-Host "Ensuring logs directory exists..."
New-Item -Path 'C:\dump_listener\logs' -ItemType Directory -Force | Out-Null

If (-not (Test-Path -Path $nssm)) {
    Write-Error "NSSM not found at: $nssm. Adjust path or install NSSM."
    exit 1
}

Write-Host "Installing service $serviceName..."
& $nssm install $serviceName $serviceBat

Write-Host "Configuring stdout/stderr and auto-start..."
& $nssm set $serviceName AppStdout $stdout
& $nssm set $serviceName AppStderr $stderr
& $nssm set $serviceName Start SERVICE_AUTO_START

Write-Host "Starting service..."
& $nssm start $serviceName

Write-Host "Service status:"
& $nssm status $serviceName

Write-Host "Done. Check logs at C:\dump_listener\logs"
