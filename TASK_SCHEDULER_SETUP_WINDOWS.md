# Running MAHA Dump Listener with Windows Task Scheduler

This guide explains how to run your Python-based dump listener as a persistent background task using Windows Task Scheduler. This is an alternative to NSSM for keeping your script running, restarting on failure, and starting at boot.

---

## Prerequisites

- Windows 10/11 or Windows Server
- Python 3.8+ installed
- Project files in `C:\dump_listener` (all scripts inside this folder)
- Virtual environment set up in `C:\dump_listener\venv`

---

## Step 1: Prepare Your Project

1. **Copy your project folder** to `C:\dump_listener`.
2. **Create a Python virtual environment:**
   ```powershell
   cd C:\dump_listener
   python -m venv venv
   venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   deactivate
   ```
3. **Edit your `.env` file** for Windows paths:
   ```env
   DUMP_DIR=C:\dump_listener\Dump
   ...other variables...
   ```
4. **Edit `config.py`** to use the environment variable:
   ```python
   from pathlib import Path
   import os
   DUMP_FOLDER = Path(os.environ.get("DUMP_DIR", r"C:\\dump_listener\\Dump"))
   PROCESSED_FOLDER = DUMP_FOLDER / "processed"
   DUMP_FOLDER.mkdir(parents=True, exist_ok=True)
   PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)
   ```

---

## Step 2: Create a Batch File to Run the Script

Create `C:\dump_listener\service.bat` with the following content:
```batch
@echo off
cd C:\dump_listener
C:\dump_listener\venv\Scripts\python.exe main.py
```

---

## Step 3: Create a Scheduled Task

### Option 1: Use Task Scheduler GUI

1. **Open Task Scheduler** (`taskschd.msc`)
2. **Create a new task:**
   - Action: "Create Task..."
   - Name: `DumpListener`
   - Description: Run MAHA Dump Listener as a background task
3. **General Tab:**
   - Select "Run whether user is logged on or not"
   - Check "Run with highest privileges"
4. **Triggers Tab:**
   - Click "New..."
   - Begin the task: "At startup" (or "On a schedule" as needed)
   - Enable "Repeat task every 1 minute" for a duration of "Indefinitely" (optional, for auto-restart)
5. **Actions Tab:**
   - Click "New..."
   - Action: "Start a program"
   - Program/script: `C:\dump_listener\service.bat`
   - Start in: `C:\dump_listener`
6. **Conditions Tab:**
   - Uncheck "Start the task only if the computer is on AC power" (if you want it to run on battery)
7. **Settings Tab:**
   - Check "Allow task to be run on demand"
   - Check "Restart the task if it fails" (set restart interval and attempts)
   - Check "If the task is already running, then the following rule applies: Stop the existing instance"
8. **OK** and enter your password if prompted.

### Option 2: Import a Predefined XML Task

1. Save the following XML as `C:\dump_listener\DumpListenerTask.xml`:

```xml
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2026-02-23T12:00:00</Date>
    <Author>MAHA</Author>
    <Description>Run MAHA Dump Listener as a background task</Description>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>Password</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>StopExisting</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>C:\dump_listener\service.bat</Command>
      <WorkingDirectory>C:\dump_listener</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
```

2. **Import the task:**
   - Open Task Scheduler
   - Action: "Import Task..."
   - Select `DumpListenerTask.xml`
   - Adjust user and password as needed

---

## Step 4: Start and Manage the Task

- **Start manually:**
  - Right-click the task and select "Run"
- **Check status:**
  - View the "Last Run Result" and "History" tabs
- **Stop the task:**
  - Right-click and select "End"
- **Edit or delete:**
  - Right-click and select "Properties" or "Delete"

---

## Step 5: Monitor Logs

```powershell
Get-Content C:\dump_listener\logs\service.log -Wait
```

---

## Troubleshooting

- **Task not starting?**
  - Check the "History" tab for errors
  - Ensure the batch file and Python environment paths are correct
  - Make sure the user account has permission to run tasks
- **Script crashes repeatedly?**
  - Check `service.log` and `service_error.log` in `C:\dump_listener\logs`
  - Use the "Restart on failure" setting in the task
- **Want to update code?**
  - Stop the task, update files, then start the task again

---

## Summary

- Task Scheduler can run your script as a persistent background task
- Supports auto-restart, start at boot, and logging
- No Docker or NSSM required

**For more info:** [Task Scheduler Documentation](https://docs.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page)
