Param(
    [string]$PythonPath = 'python',
    [string]$RepoPath = 'C:\dump_listener'
)

# Set alert recipient and other env vars here (edit before registering task)
$env:ALERT_TO = 'kemmyxy@gmail.com'
# $env:ALERT_SMTP_HOST = 'smtp.example.com'
# $env:ALERT_SMTP_USER = 'user'
# $env:ALERT_SMTP_PASS = 'pass'

Push-Location $RepoPath
try {
    & $PythonPath "$RepoPath\scripts\monitor_verification.py"
} finally {
    Pop-Location
}
