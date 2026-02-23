# Dump Listener - Deployment Guide

## Project Structure

### WSL Project (Source)
```
/home/ekarangw/dump_listener/
├── *.py (application code)
├── requirements.txt
├── .env (environment variables)
└── scripts/
    └── deploy_to_windows.sh
```

### Windows Project (Target)
```
C:\dump_listener\
├── *.py (application code)
├── requirements.txt
├── monitor.env (Windows environment variables)
├── venv\ (Python virtual environment)
├── logs\ (service logs)
└── run_service.bat (batch wrapper for NSSM)
```

## Syncing Projects

### Option 1: Auto-sync from WSL (Recommended)

Run the deploy script from WSL:
```bash
cd /home/ekarangw/dump_listener/scripts
chmod +x deploy_to_windows.sh
./deploy_to_windows.sh
```

This script:
1. Syncs all source files (WSL → C:\dump_listener)
2. Creates Windows environment file (monitor.env)
3. Creates run_service.bat wrapper
4. Sets up Python venv if needed
5. Updates NSSM service configuration

### Option 2: Manual sync

```bash
rsync -av --delete /home/ekarangw/dump_listener/ /mnt/c/dump_listener/ \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='.venv' \
  --exclude='venv' \
  --exclude='*.pyc' \
  --exclude='Dump' \
  --exclude='processed' \
  --exclude='logs'
```

## Windows Configuration

### Environment Variables (monitor.env)

The Windows service uses `C:\dump_listener\monitor.env` for environment variables:

```env
DUMP_DIR=C:\Dump
API_LOGIN_URL=https://tekana-backend-uat.pepc.rw/users-service/api/v1/auth/signin
API_URL=https://tekana-backend-uat.pepc.rw/vehicle-inspection-service/api/v1/inspectionResult/maha
API_EMAIL=admin@tekana.rw
API_PASSWORD=Qwerty@570
API_TIMEOUT=30000
```

**Important**: Do NOT use WSL paths in Windows environment. Use Windows paths (e.g., `C:\Dump` not `/mnt/c/Dump`).

### Service Startup Script (run_service.bat)

Located at `C:\dump_listener\run_service.bat`:

```batch
@echo off
cd /d C:\dump_listener
C:\dump_listener\venv\Scripts\python.exe main.py
```

This ensures:
- Working directory is set to `C:\dump_listener`
- Correct Python interpreter is used (venv)
- All relative imports work correctly

## NSSM Service Setup

### Verify Service Configuration

```powershell
# Run as Administrator
& 'C:\Program Files\nssm\win64\nssm.exe' get DumpListener Application
& 'C:\Program Files\nssm\win64\nssm.exe' get DumpListener AppParameters
& 'C:\Program Files\nssm\win64\nssm.exe' get DumpListener Start
```

Expected output:
```
C:\dump_listener\run_service.bat
(no parameters - batch file handles everything)
SERVICE_AUTO_START
```

### Service Management

```powershell
# Start service
& 'C:\Program Files\nssm\win64\nssm.exe' start DumpListener

# Stop service
& 'C:\Program Files\nssm\win64\nssm.exe' stop DumpListener

# Check status
& 'C:\Program Files\nssm\win64\nssm.exe' status DumpListener

# View logs
Get-Content 'C:\dump_listener\logs\service.log' -Tail 50
Get-Content 'C:\dump_listener\logs\service_error.log' -Tail 20
```

## Deployment Workflow

### 1. Update Code in WSL
```bash
# Make changes to code in WSL
# Test locally if needed
```

### 2. Deploy to Windows
```bash
cd /home/ekarangw/dump_listener/scripts
./deploy_to_windows.sh
```

### 3. Restart Service (if needed)
```powershell
# Run as Administrator in PowerShell
& 'C:\Program Files\nssm\win64\nssm.exe' stop DumpListener
Start-Sleep -Seconds 3
& 'C:\Program Files\nssm\win64\nssm.exe' start DumpListener
Start-Sleep -Seconds 5
& 'C:\Program Files\nssm\win64\nssm.exe' status DumpListener
```

## Troubleshooting

### Service Paused or Not Running

1. Check logs:
```powershell
Get-Content 'C:\dump_listener\logs\service_error.log'
```

2. Verify Python venv:
```powershell
& 'C:\dump_listener\venv\Scripts\python.exe' -c "import config; print('OK')"
```

3. Test script directly:
```powershell
cd C:\dump_listener
& .\venv\Scripts\python.exe main.py
```

### Import Errors

Ensure all files are synced:
```bash
rsync -av --delete /home/ekarangw/dump_listener/ /mnt/c/dump_listener/ \
  --exclude='.git' --exclude='__pycache__' --exclude='venv' --exclude='logs'
```

### Environment Variables Not Set

Verify `monitor.env` exists and is loaded by Python:
```powershell
# Python should read from PYTHONPATH
& 'C:\dump_listener\venv\Scripts\python.exe' -c "import os; print(os.environ.get('DUMP_DIR'))"
```

## Path Configuration Rules

| Component | WSL | Windows |
|-----------|-----|---------|
| Project root | `/home/ekarangw/dump_listener` | `C:\dump_listener` |
| Dump directory | `/mnt/c/Dump` (for testing) | `C:\Dump` |
| Python | `python3` | `C:\dump_listener\venv\Scripts\python.exe` |
| Env file | `.env` | `monitor.env` |
| Service executable | Direct script | `run_service.bat` (wrapper) |

## Key Files

| File | Purpose | Location |
|------|---------|----------|
| `main.py` | Entry point | Both |
| `config.py` | Reads DUMP_DIR from env | Both |
| `monitor.env` | Windows environment variables | `C:\dump_listener\` only |
| `run_service.bat` | Service wrapper | `C:\dump_listener\` only |
| `requirements.txt` | Python dependencies | Both |

## Verification Checklist

- [ ] WSL project files match Windows project files
- [ ] `C:\dump_listener\monitor.env` has correct Windows paths
- [ ] `C:\dump_listener\run_service.bat` exists and is executable
- [ ] Windows venv is installed at `C:\dump_listener\venv\`
- [ ] All Python packages installed in Windows venv
- [ ] NSSM service points to `run_service.bat`
- [ ] Service can start and read logs without errors
- [ ] Dump directory `C:\Dump\` exists

