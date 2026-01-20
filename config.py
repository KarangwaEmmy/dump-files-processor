from pathlib import Path
import os
import platform

# Use DUMP_DIR env var if provided; otherwise pick a sensible default per OS
default_dump = Path("C:\\Dump") if platform.system() == "Windows" else Path("/var/dump")
DUMP_FOLDER = Path(os.environ.get("DUMP_DIR", default_dump))

PROCESSED_FOLDER = DUMP_FOLDER / "processed"
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)

LOG_FILE = DUMP_FOLDER / "process.log"