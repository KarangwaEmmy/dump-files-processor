@echo off
REM Get-Stats.bat - Quick statistics snapshot

:loop
cls
echo ========================================
echo DUMP LISTENER - QUICK STATISTICS
echo ========================================
echo Time: %date% %time%
echo.

REM Service Status
echo [SERVICE]
powershell -Command "& 'C:\Program Files\nssm\win64\nssm.exe' status DumpListener"
echo.

REM File Counts
echo [FILES TO PROCESS]
powershell -Command "$count = @(Get-ChildItem 'C:\Dump' -File -ErrorAction SilentlyContinue).Count; Write-Host \"  Pending files: $count\""
echo.

REM Processed Count
echo [TOTAL PROCESSED]
powershell -Command "$count = @(Get-ChildItem 'C:\Dump\processed' -File -ErrorAction SilentlyContinue).Count; Write-Host \"  Total: $count\""
echo.

REM Last 3 files
echo [LAST 3 PROCESSED]
powershell -Command "Get-ChildItem 'C:\Dump\processed' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 3 | ForEach-Object { Write-Host ('  ' + $_.Name + ' [' + $_.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss') + ']') }"
echo.

REM Error Check
echo [RECENT ERRORS]
powershell -Command "@(Get-Content 'C:\dump_listener\logs\service.log' -Tail 50 -ErrorAction SilentlyContinue) | Where-Object { $_ -match 'ERROR|error|FAIL|fail' } | Select-Object -First 3 | ForEach-Object { Write-Host ('  - ' + $_) }"
echo.

echo ========================================
echo Press any key to refresh (Ctrl+C to exit)
pause >nul
goto loop
