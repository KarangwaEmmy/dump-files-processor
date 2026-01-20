<#
Usage (run as Administrator):
.\create_schtask.ps1 -PythonPath "C:\Path\To\python.exe" -AppPath "C:\Path\To\dump_listener\main.py" -WorkingDir "C:\Path\To\dump_listener"

This registers a scheduled task named 'DumpListener' that runs the Python script at system startup.
You may need to adjust paths and set execution policy to allow scripts: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine`
#>

param(
    [string]$PythonPath = "C:\\Python39\\python.exe",
    [string]$AppPath = "C:\\path\\to\\dump_listener\\main.py",
    [string]$WorkingDir = "C:\\path\\to\\dump_listener"
)

Write-Host "Registering scheduled task 'DumpListener' (AtStartup)"

$action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$AppPath`""
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest

Register-ScheduledTask -TaskName "DumpListener" -Action $action -Trigger $trigger -Principal $principal -Description "Run dump listener at system startup" -Force

Write-Host "Scheduled task created. To inspect: Get-ScheduledTask -TaskName DumpListener"
