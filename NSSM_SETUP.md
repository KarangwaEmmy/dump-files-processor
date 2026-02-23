# Running MAHA Dump Listener as a Windows Service with NSSM

This guide explains how to run your Python-based dump listener as a true Windows service using [NSSM (Non-Sucking Service Manager)](https://nssm.cc/). This ensures your script runs in the background, restarts on failure, and starts automatically at boot.

---

## Prerequisites

- Windows 10/11 or Windows Server
- Python 3.8+ installed
- Project files in `C:\DumpListener` (or your chosen folder)
- [NSSM Downloaded](https://nssm.cc/download) and extracted (e.g., `C:\Program Files\nssm`)

---

## Step 1: Prepare Your Project

1. **Copy your project folder** to `C:\DumpListener`.
2. **Create a Python virtual environment:**
   ```powershell
   cd C:\DumpListener
   python -m venv venv
   venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   deactivate
   ```
3. **Edit your `.env` file** for Windows paths:
   ```env
   DUMP_DIR=C:\DumpListener\Dump
   ...other variables...
   ```
4. **Edit `config.py`** to use the environment variable:
   ```python
   from pathlib import Path
   import os
   DUMP_FOLDER = Path(os.environ.get("DUMP_DIR", r"C:\\DumpListener\\Dump"))
   PROCESSED_FOLDER = DUMP_FOLDER / "processed"
   DUMP_FOLDER.mkdir(parents=True, exist_ok=True)
   PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)
   ```

---

## Step 2: Create a Batch File to Run the Script

Create `C:\DumpListener\service.bat` with the following content:
```batch
@echo off
cd C:\DumpListener
C:\DumpListener\venv\Scripts\python.exe main.py
```

---

## Step 3: Install NSSM and Register the Service

1. **Open PowerShell as Administrator**
2. **Navigate to NSSM folder:**
   ```powershell
   cd "C:\Program Files\nssm\win64"
   ```
3. **Install the service:**
   ```powershell
   .\nssm.exe install DumpListener "C:\DumpListener\service.bat"
   ```
   - Service name: `DumpListener`
   - Path: `C:\DumpListener\service.bat`

---

## Step 4: Configure Service Settings (Recommended)

```powershell
# Set service to auto-start
.\nssm.exe set DumpListener Start SERVICE_AUTO_START

# Restart on crash (5 second delay)
.\nssm.exe set DumpListener AppRestartDelay 5000

# Throttle restarts (prevent crash loop)
.\nssm.exe set DumpListener AppThrottle 1500

# Set log file locations
.\nssm.exe set DumpListener AppStdout "C:\DumpListener\logs\service.log"
.\nssm.exe set DumpListener AppStderr "C:\DumpListener\logs\service_error.log"
```

---

## Step 5: Start and Manage the Service

```powershell
# Start the service
.\nssm.exe start DumpListener

# Check status
.\nssm.exe status DumpListener

# Stop the service
.\nssm.exe stop DumpListener

# Restart the service
.\nssm.exe restart DumpListener
```

---

## Step 6: Monitor Logs

```powershell
Get-Content C:\DumpListener\logs\service.log -Wait
```

---

## Step 7: Remove the Service (if needed)

```powershell
.\nssm.exe remove DumpListener confirm
```

---

## Troubleshooting

- **Service not starting?**
  - Check `service.log` and `service_error.log` in `C:\DumpListener\logs`.
  - Ensure Python and all dependencies are installed in the virtual environment.
  - Make sure `.env` and `config.py` paths are correct.
- **Script crashes repeatedly?**
  - Check logs for stack traces or error messages.
  - Use `AppThrottle` to prevent rapid restart loops.
- **Want to update code?**
  - Stop the service, update files, then restart the service.

---

## Summary

- NSSM runs your script as a robust Windows service
- Auto-restarts on crash, starts at boot, logs output
- No Docker or Task Scheduler needed

**For more info:** [NSSM Documentation](https://nssm.cc/documentation)
