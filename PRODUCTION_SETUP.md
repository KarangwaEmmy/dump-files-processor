# Production Setup Guide - Dump File Listener Server

## Overview
This application is configured as a 24/7 server that monitors `C:\Dump` folder on your Windows machine for vehicle inspection dump files, processes them automatically, and sends data to an API.

## How It Works
1. **File Detection**: Monitors `C:\Dump` folder continuously (every 5 seconds via polling + real-time watchdog)
2. **Sequential Processing**: Processes one file at a time, preventing concurrent access issues
3. **Data Extraction**: Reads key=value format dump files and extracts MAHA inspection codes
4. **API Integration**: Sends structured inspection data to your API endpoint
5. **File Management**: Moves processed files to `C:\Dump\processed` folder

## System Requirements (Linux/WSL2 Host)
- Docker and Docker Compose installed
- WSL2 enabled (if running on Windows)
- `/mnt/c/Dump` accessible (Windows `C:\Dump` mounted via WSL2)

## Configuration

### .env File
```
HOST_DUMP_DIR=/mnt/c/Dump
```
This maps `C:\Dump` from Windows to the Docker container. Adjust if your dump folder is elsewhere.

## Starting the Service

### Option 1: Docker (Recommended for Linux/WSL2 host)
```bash
cd /path/to/dump_listener
docker-compose up -d --build
```

This starts the service in the background. It will:
- Monitor `/mnt/c/Dump` continuously
- Auto-restart on failure or reboot
- Keep running 24/7

### Option 2: Native Windows (Scheduled Task)
```powershell
# On Windows machine, run as Administrator:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
& "C:\dump_listener\scripts\create_schtask.ps1" -PythonPath "C:\Python311\python.exe" -AppPath "C:\dump_listener" -WorkingDir "C:\dump_listener"
```

## Monitoring

### Docker Logs
```bash
# View live logs
docker-compose logs -f dump_listener

# View last 100 lines
docker-compose logs dump_listener --tail=100
```

### Log Format
```
2026-01-20 17:41:50 | INFO | Step 3.1.1: Processing file: /app/Dump/test_polling_1.txt
2026-01-20 17:41:50 | INFO | Step 3.1.4: Payload: {'inspectionReference': 'MAHA-20260120-0815', ...}
2026-01-20 17:41:50 | INFO | Step 3.1.5: Data sent to API successfully
2026-01-20 17:41:50 | INFO | Step 3.1.6: Processing completed successfully
```

Each line has:
- `Step {run}.{file}.{step}`: Unique identifier for tracking
- Timestamps for debugging
- Detailed processing information

## Supported MAHA Codes

### Vehicle Identification
- `10100`: License Plate Number → `plateNumber`
- `10192`: Vehicle Chassis No. → `ChassisNo`
- `10201`: Vehicle Manufacturer → `manufacturer`
- `10200`: Vehicle Type → `vehicleType`
- `10190`: Number of Axles → `axleCount`
- `10107`: Inspection Date → `inspectionDate`
- `10131`: Inspection Time → `inspectionTime`
- `10512`: Inspector Name → `inspectorName`
- `10010`: Lane Number → `laneNumber`

### Test Categories
- **Brake Test**: Codes 50000-50101
- **Brake Performance**: Codes 59840, 59880, 44024
- **Side-Slip Test**: Codes 30000-30001
- **Shock Absorber**: Codes 31004-31022, 43110
- **Visual Defects**: Codes 70004, 70001
- **Emissions Test**: Codes 70024, 70021

## API Payload Structure

Each processed file generates:
```json
{
  "inspectionReference": "MAHA-20260120-0815",
  "inspectionDate": "2026-01-20T08:15:00Z",
  "source": "MAHA",
  "inspectorName": "Hassan Ali",
  "inspectionTime": "08:15",
  "plateNumber": "TEST001",
  "ChassisNo": "VIN000000000TEST001",
  "manufacturer": "FORD",
  "vehicleYype": "TRUCK",
  "axleCount": 6,
  "laneNumber": "Lane5",
  "overallResult": "PASS",
  "inspectionResults": [
    {
      "code": "10100",
      "value": "TEST001",
      "testCategory": "Vehicle Identification"
    },
    ...more test results...
  ]
}
```

## File Movement Flow
```
C:\Dump/
├── [new dump file].txt         → Detected by watcher
├── [processing].txt → [file].txt (locked during processing)
├── processed/
│   ├── [completed file].txt    → Moved here after success
│   └── ...
└── [filename].failed/           → Moved here after 3 API failures
```

## Monitoring Commands

### Check Docker Container Status
```bash
docker-compose ps
```

### View Docker Logs
```bash
# Last 50 lines
docker-compose logs --tail=50

# Follow logs in real-time
docker-compose logs -f

# Filter for API payloads
docker-compose logs | grep "Payload:"
```

### Restart Service
```bash
docker-compose restart dump_listener
```

### Stop Service
```bash
docker-compose down
```

## Troubleshooting

### Container keeps restarting
- Check logs: `docker-compose logs dump_listener`
- Check for permission issues on `/mnt/c/Dump`
- Verify PATH mappings in `.env`

### Files not being detected
- Ensure files are `.txt` format
- Check file permissions in `C:\Dump`
- Review polling logs for file detection

### API not receiving data
- Check API endpoint configuration in `api_client.py`
- Verify network connectivity from container
- Review API response in logs

### Stale lock files preventing processing
- Lock files (`.processing.lock`) are auto-cleaned after 30 seconds with PID validation
- Manual cleanup: `rm /mnt/c/Dump/.processing.lock`

## Performance
- **Polling interval**: 5 seconds (catches files watchdog might miss)
- **Sequential processing**: One file at a time
- **Concurrent safety**: File locking prevents duplicate processing
- **Retry logic**: 3 attempts per file before moving to `.failed`

## Operating Hours
- Server runs 24/7
- Optimized for 7:00 AM - 7:00 PM activity (typical inspection hours)
- Automatically processes dump files whenever they appear

## Maintenance

### View Processed Files
```bash
ls -la /mnt/c/Dump/processed/
```

### View Failed Files
```bash
ls -la /mnt/c/Dump/*.failed/
```

### Clean Old Logs
```bash
# Keep last 7 days of logs
find /mnt/c/Dump/logs -name "*.log" -mtime +7 -delete
```

## Support Files

- `config.py`: Path and environment configuration
- `main.py`: Entry point that starts the watcher
- `watcher.py`: File system monitoring with polling fallback
- `processor.py`: File parsing and API communication
- `api_client.py`: API endpoint communication
- `maha_mapping.py`: MAHA code to field mapping
- `steps.py`: Step logging for tracking execution flow
- `requirements.txt`: Python package dependencies
- `Dockerfile`: Container image definition
- `docker-compose.yml`: Container orchestration
- `.env`: Environment variables (paths)

## Updates

To deploy updates:
1. Make code changes
2. Rebuild: `docker-compose up -d --build`
3. Verify: `docker-compose logs -f`
4. No downtime - new container replaces old one seamlessly
