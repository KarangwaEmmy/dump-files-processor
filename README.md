# MAHA Dump File Listener & API Integration

Automated dump file processor that monitors a directory for inspection dump files, extracts MAHA codes, and submits structured data to the Tekana Vehicle Inspection API with JWT authentication.

## Features

✅ **24/7 File Monitoring**
- Real-time detection of dump files via watchdog
- Polling fallback for network shares (WSL2/mounted volumes)
- Sequential processing with file locking to prevent duplicates

✅ **MAHA Code Mapping**
- 35+ vehicle inspection codes supported
- Automatic extraction and categorization
- Support for Vehicle Identification, Brake Test, Shock Absorber, Emissions, and more

✅ **API Integration**
- JWT Bearer token authentication
- Automatic token refresh on expiration (24-hour window)
- Retry logic with re-authentication on 401 Unauthorized
- Structured payload building matching API schema

✅ **Production Ready**
- Docker containerization for easy deployment
- Windows service integration (NSSM)
- Environment-based configuration
- Comprehensive logging and error handling
- File locking to prevent concurrent processing

---

## Installation

### Prerequisites

- **For Docker:** Docker Desktop (Windows/Mac/Linux)
- **For Native Windows:** Python 3.11+ and pip

### Quick Start - Docker (Recommended)

1. **Clone/copy project:**
```bash
git clone <repository>
cd dump_listener
```

2. **Configure environment (`.env`):**
```bash
HOST_DUMP_DIR=/mnt/c/Dump          # Windows C:\Dump via WSL2
API_LOGIN_URL=https://tekana-backend-uat.pepc.rw/users-service/api/v1/auth/signin
API_URL=https://tekana-backend-uat.pepc.rw/vehicle-inspection-service/api/v1/inspectionResult/maha
API_EMAIL=your-email@example.com
API_PASSWORD=your-secure-password
API_TIMEOUT=30000
```

3. **Start container:**
```bash
docker-compose up -d
```

4. **View logs:**
```bash
docker-compose logs -f dump_listener
```

### Native Setup - Linux/Mac

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure .env
cp .env.example .env
nano .env

# Run
python main.py
```

---

## Production Deployment

### Option 1: Docker Desktop on Windows (BEST FOR INTRANET)

**Advantages:**
- Same configuration as development
- Automatic container restart on failure
- Easy to update and manage
- Native Windows integration

**Setup:**

1. Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

2. Update `docker-compose.yml` for network shares:
```yaml
volumes:
  - "\\\\server\\shared_folder\\Dump:/app/Dump"  # Network UNC path
  - "./logs:/app/logs"
```

3. Set Docker to auto-start:
   - Settings → General → "Start Docker Desktop when you log in"

4. Create startup batch file (`C:\DumpListener\start.bat`):
```batch
@echo off
cd C:\DumpListener
docker-compose up -d
echo Dump Listener started
```

5. Add to Task Scheduler:
   - Task Scheduler → Create Basic Task
   - Trigger: At startup
   - Action: Run `C:\DumpListener\start.bat`

---

### Option 2: Windows Service with NSSM (FREE & NATIVE) ⭐ RECOMMENDED

**Best for:** True Windows server integration without Docker + Perfect for PC simulation testing

---

#### Step 1: Copy Project to Windows PC

Copy the entire project folder to your Windows PC: `C:\DumpListener`

**Required files:**
```
C:\DumpListener\
├── main.py
├── processor.py
├── api_client.py
├── auth.py
├── watcher.py
├── config.py
├── maha_mapping.py
├── steps.py
├── requirements.txt
├── .env
├── README.md
└── .gitignore
```

---

#### Step 2: Download & Setup NSSM

1. **Download NSSM:**
   - Visit: https://nssm.cc/download
   - Download latest version (e.g., `nssm-2.24-104-g01d7a2f.zip`)
   - Extract to: `C:\Program Files\nssm`

2. **Verify NSSM installation:**
```powershell
# Open PowerShell as Administrator
"C:\Program Files\nssm\win64\nssm.exe" status
```

---

#### Step 3: Setup Python Virtual Environment on Windows PC

```powershell
# Open PowerShell as Administrator
cd C:\DumpListener

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Verify key packages installed
pip list | grep watchdog
pip list | grep requests

# Exit virtual environment
deactivate
```

---

#### Step 4: Update `.env` for Windows Paths

Edit `C:\DumpListener\.env`:

```bash
# CHANGE THIS LINE:
HOST_DUMP_DIR=/mnt/c/Dump

# TO THIS (Windows local path):
DUMP_DIR=C:\DumpListener\Dump

# KEEP THESE AS-IS (already configured):
API_LOGIN_URL=https://tekana-backend-uat.pepc.rw/users-service/api/v1/auth/signin
API_URL=https://tekana-backend-uat.pepc.rw/vehicle-inspection-service/api/v1/inspectionResult/maha
API_EMAIL=admin@tekana.rw
API_PASSWORD=Qwerty@570
API_TIMEOUT=30000
```

---

#### Step 5: Update `config.py` for Windows

Edit `C:\DumpListener\config.py` to ensure it reads from environment:

```python
from pathlib import Path
import os

# Read from .env environment variable
DUMP_FOLDER = Path(os.environ.get("DUMP_DIR", r"C:\DumpListener\Dump"))
PROCESSED_FOLDER = DUMP_FOLDER / "processed"

# Ensure folders exist
DUMP_FOLDER.mkdir(parents=True, exist_ok=True)
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)
```

---

#### Step 6: Create Service Batch File

Create file: `C:\DumpListener\service.bat`

```batch
@echo off
cd C:\DumpListener
C:\DumpListener\venv\Scripts\python.exe main.py
```

---

#### Step 7: Register Windows Service with NSSM

```powershell
# Open PowerShell as Administrator
cd "C:\Program Files\nssm\win64"

# Register the service
.\nssm.exe install DumpListener "C:\DumpListener\service.bat"

# Configure service to auto-start on PC boot
.\nssm.exe set DumpListener Start SERVICE_AUTO_START

# Set restart on crash (5 second delay)
.\nssm.exe set DumpListener AppRestartDelay 5000

# Set throttle (prevent crash loop)
.\nssm.exe set DumpListener AppThrottle 1500

# Set log file locations
.\nssm.exe set DumpListener AppStdout "C:\DumpListener\logs\service.log"
.\nssm.exe set DumpListener AppStderr "C:\DumpListener\logs\service_error.log"

# Start the service
.\nssm.exe start DumpListener
```

---

#### Step 8: Verify Service is Running

```powershell
# Check service status
"C:\Program Files\nssm\win64\nssm.exe" status DumpListener
# Should output: SERVICE_RUNNING

# View real-time logs
Get-Content C:\DumpListener\logs\service.log -Wait
```

---

#### Step 9: Test with Sample Dump Files

1. **Create test directory:**
```powershell
New-Item -ItemType Directory -Path "C:\DumpListener\Dump" -Force
```

2. **Create sample dump file:** `C:\DumpListener\Dump\test_vehicle.txt`
```
10100=ABC123
10192=123456
10201=Toyota
10200=Sedan
10190=2
10512=John Doe
10010=1
10107=20260121
10131=10:30
30000=2.5
50000=25.0
59840=85.0
```

3. **Watch service logs:**
```powershell
Get-Content C:\DumpListener\logs\service.log -Wait
```

**Expected output:**
```
✅ Step 1: API Login successful - Token expires: 2026-01-22 10:14:38
✅ Step 2: Dump folder watcher started
✅ File detected: test_vehicle.txt
✅ Processing file: test_vehicle.txt
✅ Built payload with 3 results
✅ Data sent to API successfully
✅ Processing completed successfully
```

4. **Verify processed file:**
```powershell
Get-ChildItem C:\DumpListener\Dump\processed\
# Should show: test_vehicle.txt
```

---

#### Service Management Commands

```powershell
# Check status
"C:\Program Files\nssm\win64\nssm.exe" status DumpListener

# Start service
"C:\Program Files\nssm\win64\nssm.exe" start DumpListener

# Stop service
"C:\Program Files\nssm\win64\nssm.exe" stop DumpListener

# Restart service
"C:\Program Files\nssm\win64\nssm.exe" restart DumpListener

# View real-time logs (PowerShell)
Get-Content C:\DumpListener\logs\service.log -Wait

# View last 50 lines
Get-Content C:\DumpListener\logs\service.log | Select-Object -Last 50

# Search for errors
Select-String "ERROR" C:\DumpListener\logs\service.log

# Remove service (when no longer needed)
"C:\Program Files\nssm\win64\nssm.exe" remove DumpListener confirm
```

---

### Option 3: Python Windows Service (Advanced)

Create a true Windows service using `pywin32`:

```python
# service_wrapper.py
import win32serviceutil
import win32service
import win32event
import servicemanager
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from main import start_watcher

class DumpListenerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "DumpListener"
    _svc_display_name_ = "MAHA Dump File Listener Service"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.isAlive = True

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        start_watcher()

    def SvcStop(self):
        self.isAlive = False

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(DumpListenerService)
```

Install:
```bash
pip install pywin32
python service_wrapper.py install
python service_wrapper.py start
```

---

## Configuration

### Environment Variables (`.env`)

```bash
# Directory Monitoring
HOST_DUMP_DIR=/mnt/c/Dump           # Docker: WSL2 mount path
DUMP_DIR=C:\DumpListener\Dump       # Windows: local or UNC path

# API Configuration
API_LOGIN_URL=https://tekana-backend-uat.pepc.rw/users-service/api/v1/auth/signin
API_URL=https://tekana-backend-uat.pepc.rw/vehicle-inspection-service/api/v1/inspectionResult/maha
API_EMAIL=admin@tekana.rw
API_PASSWORD=Qwerty@570
API_TIMEOUT=30000
```

### Network File Sharing

**Option A: Map Network Drive (GUI)**
1. File Explorer → Map Network Drive
2. Path: `\\server\shared_folder`
3. Letter: `Z:`
4. Check "Reconnect at sign-in"

**Option B: Persistent Mapping (PowerShell Admin)**
```powershell
$password = ConvertTo-SecureString "your-password" -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential("domain\user", $password)
New-PSDrive -Name Z -PSProvider FileSystem -Root "\\server\shared_folder" `
  -Credential $credential -Persist
```

**Option C: UNC Path (Direct)**
```
\\server\shared_folder\Dump
```

---

## API Integration

### Authentication Flow

1. **Startup:** System authenticates with API using credentials from `.env`
2. **Token Storage:** JWT token stored in memory with 24-hour expiration
3. **File Processing:** Each payload sent includes Bearer token in Authorization header
4. **Auto-Refresh:** If token expires, system automatically re-authenticates
5. **Retry Logic:** On 401 Unauthorized, attempts login and retries the request

### API Endpoints

**Login Endpoint:**
```
POST https://tekana-backend-uat.pepc.rw/users-service/api/v1/auth/signin
Body: {"login": "email@example.com", "password": "password"}
Response: {"token": {"accessToken": "JWT_STRING", "tokenType": "Bearer"}}
```

**Data Submission Endpoint:**
```
POST https://tekana-backend-uat.pepc.rw/vehicle-inspection-service/api/v1/inspectionResult/maha
Headers: {"Authorization": "Bearer JWT_TOKEN", "Content-Type": "application/json"}
Body: {inspection payload}
```

### Payload Structure

```json
{
  "inspectionReference": "MAHA-20260121-102926",
  "inspectionDate": "2026-01-21T10:29:26.000Z",
  "source": "MAHA",
  "inspectorName": "Inspector Name",
  "inspectionTime": "10:29",
  "plateNumber": "ABC123",
  "chassisNo": 123456,
  "manufacturer": "Toyota",
  "vehicleType": "Sedan",
  "axleCount": 2,
  "laneNumber": "1",
  "overallResult": "PASS",
  "inspectionResults": [
    {"code": "30000", "value": 2.5, "testCategory": "Side-Slip Test"},
    {"code": "50000", "value": 25.0, "testCategory": "Brake Test"},
    {"code": "59840", "value": 85.0, "testCategory": "Brake Performance"}
  ]
}
```

---

## Monitoring & Logging

### Docker Logs

```bash
# Real-time logs
docker-compose logs -f dump_listener

# Last 100 lines
docker-compose logs dump_listener --tail=100

# Grep for errors
docker-compose logs dump_listener | grep ERROR

# Grep for API responses
docker-compose logs dump_listener | grep "API error\|Data sent"
```

### Windows Service Logs

```bash
# View service log (PowerShell)
Get-Content C:\DumpListener\logs\service.log -Wait

# Tail last 50 lines
Get-Content C:\DumpListener\logs\service.log | Select-Object -Last 50

# Search for errors
Select-String "ERROR" C:\DumpListener\logs\service.log

# Search for successful API submissions
Select-String "Data sent to API successfully" C:\DumpListener\logs\service.log
```

### Log Rotation

Add to `main.py` for automatic log rotation:

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/dump_listener.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5            # Keep 5 backup files
)
```

---

## Appointment Error Handling

When a dump file is processed and the API returns **"No validated appointment found for plate number"** error, the system automatically:

1. **Detects** the appointment validation error from API response
2. **Moves** the file to the `Appointment` folder
3. **Names** it with timestamp format: `YYYY-MM-DD_HH-MM-SS_originalname.txt`

**Example flow:**

```
Dump folder (initial):
└── ES_OUT_NEW.txt

Processing:
1. File sent to API
2. API returns: {"message": "No validated appointment found for plate number: RAF597V"}
3. System detects error
4. File moved to Appointment folder

Result:
└── Appointment/
    └── 2026-01-22_08-00-02_ES_OUT_NEW.txt
```

**Action Required:**

Files in the `Appointment` folder indicate that:
- ✅ File was successfully processed
- ✅ Data was sent to API
- ❌ **Appointment does not exist in Tekana system for that plate number**

**Next Steps:**
1. Create the appointment in Tekana backend for the plate number
2. Manually move the file back to the Dump folder
3. System will retry processing with new appointment

---

## Running Forever - Best Practices

The system processes these inspection result categories:

- **Side-Slip Test** (30000, 30001)
- **Shock Absorber Test** (31004-31022, 43110)
- **Brake Test** (50000, 50001, 50010, 50100, 50101, 50110)
- **Parking Brake** (59000, 59010, 59020)
- **Brake Performance** (59840, 59880, 44024)
- **Visual Defects** (70004, 70001)
- **Emissions Test** (70024, 70021)

Vehicle Identification codes (10100, 10192, 10512, etc.) are extracted to top-level fields.

---

## Troubleshooting

### Service won't start

```bash
# Check service status
nssm status DumpListener

# View detailed error log
Get-Content C:\DumpListener\logs\service_error.log

# Restart service
nssm restart DumpListener

# Check if Python venv is accessible
C:\DumpListener\venv\Scripts\python --version
```

### Network share not accessible

```bash
# Test UNC path
Test-Path \\server\shared_folder\Dump

# Check credentials
Get-PSDrive | Select-Object Name, Root

# Reconnect drive
net use Z: \\server\shared_folder /persistent:yes
```

### API authentication failing

```bash
# Check .env credentials
type C:\DumpListener\.env

# Test API endpoint
curl -X POST "https://tekana-backend-uat.pepc.rw/users-service/api/v1/auth/signin" `
  -H "Content-Type: application/json" `
  -d "{\"login\":\"admin@tekana.rw\",\"password\":\"Qwerty@570\"}"

# Check logs for authentication errors
Select-String "Login error\|authentication" C:\DumpListener\logs\service.log
```

### Files not being processed

1. Check file is in dump directory:
   ```bash
   Get-ChildItem \\server\shared_folder\Dump\*.txt
   ```

2. Check for lock file:
   ```bash
   Get-ChildItem \\server\shared_folder\Dump\.processing.lock
   ```

3. View service logs:
   ```bash
   Get-Content C:\DumpListener\logs\service.log | Select-Object -Last 30
   ```

4. Verify file permissions:
   ```bash
   icacls \\server\shared_folder\Dump
   ```

---

## Running Forever - Best Practices

### 1. **Automatic Restart on Crash**

**NSSM:**
```bash
nssm set DumpListener AppRestartDelay 5000    # 5 second delay
nssm set DumpListener AppThrottle 1500        # Throttle if crashing
```

**Docker:**
```yaml
services:
  dump_listener:
    restart: always
    environment:
      - PYTHONUNBUFFERED=1
```

### 2. **Auto-start on Server Boot**

**NSSM:**
```bash
nssm set DumpListener Start SERVICE_AUTO_START
```

**Docker:**
- Windows Task Scheduler → Create task to run `docker-compose up -d` at startup

### 3. **Connection Resilience**

Built-in features:
- Automatic token refresh
- 3 retries on API failure with 1-second delays
- File locking prevents duplicate processing
- Graceful handling of network errors

### 4. **Monitoring & Health Checks**

```bash
# Weekly log review
Get-ChildItem C:\DumpListener\logs\ | Sort-Object LastWriteTime -Descending | Select-Object -First 1

# Check service status
Get-Service DumpListener | Select-Object Name, Status, StartType

# Monitor disk space
Get-Volume Z: | Select-Object SizeRemaining, Size
```

### 5. **Database of Processed Files**

Files are moved to `Dump\processed\` after successful submission:
```bash
# Count processed files
(Get-ChildItem \\server\shared_folder\Dump\processed\).Count

# List recent processed files
Get-ChildItem \\server\shared_folder\Dump\processed\ | Sort-Object LastWriteTime -Descending | Select-Object -First 10

# Archive old files (monthly)
Get-ChildItem \\server\shared_folder\Dump\processed\ | Where-Object {$_.LastWriteTime -lt (Get-Date).AddMonths(-1)} | Move-Item -Destination \\server\archive\
```

---

## Support & Troubleshooting

For issues:
1. Check logs: `C:\DumpListener\logs\service.log`
2. Verify `.env` configuration
3. Test API connectivity
4. Check network share accessibility
5. Review file permissions

---

## License

© 2026 Tekana Vehicle Inspection System. All rights reserved.
