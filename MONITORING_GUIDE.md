# Real-Time Monitoring Guide for Dump Listener Service

## Quick Commands (Run on Windows)

### 1. CHECK SERVICE STATUS
```powershell
& 'C:\Program Files\nssm\win64\nssm.exe' status DumpListener
```

### 2. COUNT PENDING FILES
```powershell
(Get-ChildItem 'C:\Dump' -File).Count
```

### 3. COUNT PROCESSED FILES
```powershell
(Get-ChildItem 'C:\Dump\processed' -File).Count
```

### 4. VIEW LAST 10 LOG LINES
```powershell
Get-Content 'C:\dump_listener\logs\service.log' -Tail 10
```

### 5. WATCH LOG LIVE (New lines as they appear)
```powershell
Get-Content 'C:\dump_listener\logs\service.log' -Wait -Tail 0
```

### 6. SHOW LAST 5 PROCESSED FILES WITH TIMESTAMPS
```powershell
Get-ChildItem 'C:\Dump\processed' -File | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | Format-Table Name, LastWriteTime
```

### 7. FILTER ERRORS IN LOG
```powershell
Get-Content 'C:\dump_listener\logs\service.log' -Tail 50 | Where-Object { $_ -match 'ERROR|error|FAIL|fail' }
```

### 8. FILTER SUCCESS MESSAGES IN LOG
```powershell
Get-Content 'C:\dump_listener\logs\service.log' -Tail 50 | Where-Object { $_ -match 'sent|SUCCESS|Processed' }
```

### 9. VIEW .ENV FILE (Check credentials and paths)
```powershell
Get-Content 'C:\dump_listener\.env'
```

### 10. RESTART SERVICE
```powershell
& 'C:\Program Files\nssm\win64\nssm.exe' restart DumpListener
```

---

## PRE-MADE MONITORING SCRIPTS

### OPTION A: PowerShell Dashboard (Best for real-time monitoring)
```
powershell -ExecutionPolicy Bypass -File C:\dump_listener\Monitor-DumpListener.ps1
```
- Shows: Service status, file counts, last 5 processed files, recent log entries
- Auto-refreshes every 5 seconds
- Color-coded for easy reading

### OPTION B: Batch Log Viewer
```
C:\dump_listener\Watch-Logs.bat
```
- Continuous live log viewing
- Color highlights for errors (red) and successes (green)
- Auto-refresh every 3 seconds

### OPTION C: Quick Stats
```
C:\dump_listener\Get-Stats.bat
```
- One-time snapshot of current state
- Shows service status, file counts, recent errors
- Press any key to refresh

---

## WHAT THE SERVICE IS DOING

Look for these patterns in the logs to understand the flow:

### File Detection
```
[MARKER] Detected new file in dump directory: C:\Dump\FILENAME.txt
```

### API Communication
```
[TYPE 1.X.X] Attempting API call
[TYPE 1.X.X] API Response received
```

### File Processing
```
[MARKER] Sent data to API for: FILENAME.txt
[MARKER] Data successfully processed
[MARKER] File moved to: C:\Dump\processed\FILENAME.txt
```

### Errors (if any)
```
ERROR: API request failed
FAIL: Cannot connect to API_LOGIN_URL
CONNECTION ERROR: Timeout
```

---

## REAL-TIME MONITORING WORKFLOW

### Step 1: Start the PowerShell Monitor
```
powershell -ExecutionPolicy Bypass -File C:\dump_listener\Monitor-DumpListener.ps1
```

### Step 2: In Another PowerShell Window, Watch API Logs
```
Get-Content 'C:\dump_listener\logs\service.log' -Wait -Tail 0
```

### Step 3: Monitor File Movement
- Watch C:\Dump for new files being received
- Watch files disappear as they're processed
- Watch files appear in C:\Dump\processed

---

## KEY METRICS TO MONITOR

| Metric | What It Means |
|--------|---------------|
| Files in C:\Dump | Files waiting to be processed |
| Files in C:\Dump\processed | Total files successfully processed |
| Service Status = SERVICE_RUNNING | Service is actively monitoring |
| "sent to API" in logs | Files being sent to your API |
| Recent processed timestamps | How actively the service is working |
| ERROR lines | Problems that need attention |

---

## TROUBLESHOOTING

### If service shows SERVICE_STOPPED
1. Check the log: `Get-Content 'C:\dump_listener\logs\service.log' -Tail 50`
2. Look for ERROR lines
3. Restart: `& 'C:\Program Files\nssm\win64\nssm.exe' start DumpListener`

### If files aren't being processed
1. Check if .env file exists: `Test-Path 'C:\dump_listener\.env'`
2. Check if C:\Dump exists: `Test-Path 'C:\Dump'`
3. Check if API credentials in .env are correct
4. Look in logs for API connection errors

### If API calls are failing
1. Check .env file: `Get-Content 'C:\dump_listener\.env'`
2. Verify API credentials are correct
3. Check network connectivity
4. Look for "ERROR" in logs: `Get-Content 'C:\dump_listener\logs\service.log' -Tail 100 | Where-Object { $_ -match 'ERROR' }`

---

## RECOMMENDED MONITORING SETUP

### For continuous 24/7 monitoring:
1. Keep Monitor-DumpListener.ps1 running on a secondary screen
2. Check it periodically throughout the day
3. Receive notifications if files stop being processed

### For active development/testing:
1. Run Watch-Logs.bat to see all API communication in real-time
2. Put test files in C:\Dump
3. Watch them move to C:\Dump\processed
4. See API responses in the logs immediately

### For daily check-ins:
1. Run Get-Stats.bat
2. Verify service is running
3. Confirm recent files were processed
4. Check for any errors in the last 50 entries
