<#
Register a scheduled task that runs the monitor wrapper daily at a given time.

Usage (run as Administrator):
  powershell -ExecutionPolicy Bypass -File scripts/windows/register_schtask.ps1 -Time "02:00"

This creates a task named "DumpListenerMonitor" that will run as the current user.
Edit `run_monitor_wrapper.ps1` to set `ALERT_TO` and SMTP settings before registering.
#>

param(
    [string]$Time = "02:00",
    [string]$TaskName = "DumpListenerMonitor",
    [string]$Wrapper = "$PSScriptRoot\run_monitor_wrapper.ps1"
)

if (-not (Test-Path $Wrapper)) {
    Write-Error "Wrapper script not found: $Wrapper"
    exit 1
}

$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Wrapper`""
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Force
Write-Output "Registered scheduled task '$TaskName' to run daily at $Time"
