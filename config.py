from pathlib import Path
import os
import platform

# Use DUMP_DIR env var if provided; otherwise pick a sensible default per OS
default_dump = Path("C:\\Dump") if platform.system() == "Windows" else Path("/var/dump")
DUMP_FOLDER = Path(os.environ.get("DUMP_DIR", default_dump))

PROCESSED_FOLDER = DUMP_FOLDER / "processed"
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)

LOG_FILE = DUMP_FOLDER / "process.log"
# Optional HMAC secret used to verify incoming dumps. Keep this secret on the server.
HMAC_SECRET = os.environ.get('HMAC_SECRET')

# Verification and alert logs
VERIFICATION_LOG = DUMP_FOLDER / "verification.log"
ALERT_LOG = DUMP_FOLDER / "alerts.log"

# Threshold for raising an alert on repeated verification failures (default: 3)
ALERT_THRESHOLD = int(os.environ.get('ALERT_THRESHOLD', '3'))

# State file to track repeated failures
STATE_FILE = DUMP_FOLDER / ".verification_state.json"