# Monitor-DumpListener.ps1
# Real-time monitoring dashboard for Dump Listener Service
# Run: powershell -ExecutionPolicy Bypass -File C:\dump_listener\Monitor-DumpListener.ps1

param(
    [int]$RefreshInterval = 5
)

while($true) {
    Clear-Host
    
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║          DUMP LISTENER REAL-TIME MONITORING               ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
    Write-Host ""
    
    # Service Status
    Write-Host "┌─ SERVICE STATUS ─────────────────────────────────────────────┐" -ForegroundColor Green
    $status = & 'C:\Program Files\nssm\win64\nssm.exe' status DumpListener
    $statusColor = if ($status -eq "SERVICE_RUNNING") { "Green" } else { "Red" }
    Write-Host "  Status: $status" -ForegroundColor $statusColor
    Write-Host "└────────────────────────────────────────────────────────────────┘" -ForegroundColor Green
    Write-Host ""
    
    # File Counts
    Write-Host "┌─ FILE PROCESSING ─────────────────────────────────────────────┐" -ForegroundColor Magenta
    try {
        $sourceCount = @(Get-ChildItem 'C:\Dump' -File -ErrorAction SilentlyContinue).Count
        $processedCount = @(Get-ChildItem 'C:\Dump\processed' -File -ErrorAction SilentlyContinue).Count
        Write-Host "  Pending in C:\Dump:           $sourceCount files" -ForegroundColor White
        Write-Host "  Total processed:              $processedCount files" -ForegroundColor White
        
        if ($sourceCount -gt 0) {
            Write-Host "  STATUS: ⚙️  ACTIVELY PROCESSING" -ForegroundColor Yellow
        } else {
            Write-Host "  STATUS: ✓ Waiting for files" -ForegroundColor Green
        }
    } catch {
        Write-Host "  Error reading directories: $_" -ForegroundColor Red
    }
    Write-Host "└────────────────────────────────────────────────────────────────┘" -ForegroundColor Magenta
    Write-Host ""
    
    # Last 5 Processed Files
    Write-Host "┌─ LAST 5 PROCESSED FILES ──────────────────────────────────────┐" -ForegroundColor Cyan
    try {
        $recentFiles = @(Get-ChildItem 'C:\Dump\processed' -File -ErrorAction SilentlyContinue | 
                         Sort-Object LastWriteTime -Descending | 
                         Select-Object -First 5)
        
        if ($recentFiles.Count -eq 0) {
            Write-Host "  No files processed yet" -ForegroundColor Gray
        } else {
            foreach ($file in $recentFiles) {
                $timeAgo = (Get-Date) - $file.LastWriteTime
                $since = ""
                if ($timeAgo.TotalSeconds -lt 60) { $since = "$(([int]$timeAgo.TotalSeconds))s ago" }
                elseif ($timeAgo.TotalMinutes -lt 60) { $since = "$(([int]$timeAgo.TotalMinutes))m ago" }
                else { $since = "$(([int]$timeAgo.TotalHours))h ago" }
                
                Write-Host "  ✓ $($file.Name)" -ForegroundColor Green -NoNewline
                Write-Host " [$since]" -ForegroundColor Gray
            }
        }
    } catch {
        Write-Host "  Error reading processed files: $_" -ForegroundColor Red
    }
    Write-Host "└────────────────────────────────────────────────────────────────┘" -ForegroundColor Cyan
    Write-Host ""
    
    # Logs Preview
    Write-Host "┌─ RECENT LOG ENTRIES ──────────────────────────────────────────┐" -ForegroundColor Blue
    try {
        $logPath = 'C:\dump_listener\logs\service.log'
        if (Test-Path $logPath) {
            $logLines = @(Get-Content $logPath -Tail 3 -ErrorAction SilentlyContinue)
            foreach ($line in $logLines) {
                if ($line -match "ERROR|FAIL" -or $line -match "error|fail") {
                    Write-Host "  ✗ $line" -ForegroundColor Red -NoNewline
                } elseif ($line -match "SUCCESS|sent|Processed" -or $line -match "success") {
                    Write-Host "  ✓ $line" -ForegroundColor Green -NoNewline
                } else {
                    Write-Host "  • $line" -ForegroundColor White -NoNewline
                }
                Write-Host ""
            }
        } else {
            Write-Host "  Log file not found" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  Error reading log: $_" -ForegroundColor Red
    }
    Write-Host "└────────────────────────────────────────────────────────────────┘" -ForegroundColor Blue
    Write-Host ""
    
    Write-Host "Refreshing every $RefreshInterval seconds (Press Ctrl+C to exit)" -ForegroundColor Gray
    Start-Sleep -Seconds $RefreshInterval
}
