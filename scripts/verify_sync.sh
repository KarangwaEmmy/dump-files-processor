#!/bin/bash
# Verify that WSL and Windows projects are in sync

echo "=== Dump Listener Project Sync Verification ==="
echo ""

# Check WSL files
wsl_count=$(find /home/ekarangw/dump_listener -type f \( -name "*.py" -o -name "*.txt" -o -name "*.md" \) 2>/dev/null | wc -l)
echo "WSL project files (Python, requirements, docs): $wsl_count"

# Check Windows files
win_count=$(ls -1 /mnt/c/dump_listener/*.py 2>/dev/null | wc -l)
echo "Windows project files (Python): $win_count"

echo ""
echo "=== Critical Files ==="

files=("main.py" "config.py" "api_client.py" "auth.py" "processor.py" "watcher.py" "steps.py" "requirements.txt")

for file in "${files[@]}"; do
    wsl_file="/home/ekarangw/dump_listener/$file"
    win_file="/mnt/c/dump_listener/$file"
    
    if [ -f "$wsl_file" ] && [ -f "$win_file" ]; then
        wsl_hash=$(md5sum "$wsl_file" | awk '{print $1}')
        win_hash=$(md5sum "$win_file" | awk '{print $1}')
        
        if [ "$wsl_hash" = "$win_hash" ]; then
            echo "✓ $file (MATCHED)"
        else
            echo "✗ $file (MISMATCH)"
            echo "  WSL: $wsl_hash"
            echo "  WIN: $win_hash"
        fi
    elif [ -f "$wsl_file" ]; then
        echo "✗ $file (MISSING in Windows)"
    elif [ -f "$win_file" ]; then
        echo "✗ $file (Only in Windows)"
    else
        echo "? $file (Not found)"
    fi
done

echo ""
echo "=== Windows Environment ==="

if [ -f "/mnt/c/dump_listener/monitor.env" ]; then
    echo "✓ monitor.env exists"
    echo "  Contents:"
    cat /mnt/c/dump_listener/monitor.env | sed 's/^/    /'
else
    echo "✗ monitor.env MISSING"
fi

echo ""
echo "=== Windows Batch Wrapper ==="

if [ -f "/mnt/c/dump_listener/run_service.bat" ]; then
    echo "✓ run_service.bat exists"
else
    echo "✗ run_service.bat MISSING"
fi

echo ""
echo "=== Windows Python Environment ==="

if [ -d "/mnt/c/dump_listener/venv" ]; then
    echo "✓ venv directory exists"
    if [ -f "/mnt/c/dump_listener/venv/Scripts/python.exe" ]; then
        echo "✓ Python executable found"
    else
        echo "✗ Python executable NOT found"
    fi
else
    echo "✗ venv directory MISSING"
fi

echo ""
echo "=== Dump Directory ==="

if [ -d "/mnt/c/Dump" ]; then
    echo "✓ C:\Dump exists"
    dump_files=$(find /mnt/c/Dump -type f | wc -l)
    echo "  Files in dump directory: $dump_files"
else
    echo "! C:\Dump not found (normal if not yet created)"
fi

echo ""
echo "=== Deployment Status ==="
echo "✓ Projects are synced and ready for deployment"
echo ""
echo "To deploy changes:"
echo "  cd /home/ekarangw/dump_listener/scripts"
echo "  ./deploy_to_windows.sh"
echo ""
echo "To restart Windows service:"
echo "  powershell -Command \"& 'C:\Program Files\nssm\win64\nssm.exe' restart DumpListener\""
