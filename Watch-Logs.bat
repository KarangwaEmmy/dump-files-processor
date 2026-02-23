@echo off
REM Watch-Logs.bat - Real-time log viewer
REM Run this in Command Prompt to watch logs live as they're written

echo.
echo ========================================
echo DUMP LISTENER LOG MONITORING
echo ========================================
echo.
echo Watching: C:\dump_listener\logs\service.log
echo Ctrl+C to stop
echo.

:watch_loop
cls
echo [%date% %time%] DUMP LISTENER SERVICE LOG TAIL (Last 20 lines)
echo -----------------------------------------------------------
echo.
powershell -Command "$content = Get-Content 'C:\dump_listener\logs\service.log' -Tail 20 -ErrorAction SilentlyContinue; foreach ($line in $content) { if ($line -match 'ERROR\|FAIL\|error\|fail') { Write-Host $line -ForegroundColor Red } elseif ($line -match 'SUCCESS\|sent\|Processed\|success') { Write-Host $line -ForegroundColor Green } else { Write-Host $line } }"
echo.
echo -----------------------------------------------------------
echo Refreshing in 3 seconds... (Press Ctrl+C to exit)
echo.
timeout /t 3 /nobreak
goto watch_loop
