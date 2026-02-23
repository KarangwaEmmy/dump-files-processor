# Deploy to Windows (one-click)

Use `deploy_to_windows.sh` from WSL to copy the current workspace to `C:\dump_listener`, create `C:\Dump`, and prepare a Windows virtual environment.

Quick steps (WSL):

```bash
cd /home/ekarangw/dump_listener/scripts
chmod +x deploy_to_windows.sh
./deploy_to_windows.sh
```

What the script now does (improved, step-by-step):
- Step 1: create `C:\dump_listener` on Windows
- Step 2: ensure `C:\Dump` exists (dump folder outside project)
- Step 3: rsync the repo to `C:\dump_listener` (excludes `.git`, `venv`, etc.)
- Step 4: create `C:\dump_listener\monitor.env` with `DUMP_DIR=C:\Dump`
- Step 5: create `C:\dump_listener\service.bat` to run `main.py` using the Windows venv
- Step 6: drop `C:\dump_listener\setup_windows_env.ps1` and invoke it to create `venv` and install packages

After deploy - verification commands (Windows PowerShell):

```powershell
# check python in venv
C:\dump_listener\venv\Scripts\python.exe --version

# view environment file
Get-Content C:\dump_listener\monitor.env

# ensure dump folder exists
Get-ChildItem C:\ | Where-Object Name -eq 'Dump'
```

To run as a service use NSSM (see NSSM_SETUP_WINDOWS.md) or Task Scheduler (see TASK_SCHEDULER_SETUP_WINDOWS.md).

If you want to skip the automatic PowerShell step from WSL, run the `setup_windows_env.ps1` manually on Windows:

```powershell
cd C:\dump_listener
PowerShell -NoProfile -ExecutionPolicy Bypass -File .\setup_windows_env.ps1
```
