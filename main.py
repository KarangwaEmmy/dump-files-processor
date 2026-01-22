import logging
from config import DUMP_FOLDER
from watcher import start_watcher
from steps import step, reset
from auth import login

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/service.log"),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    reset()
    step(f"Dump folder watcher starting (watching: {DUMP_FOLDER})")
    
    # Authenticate with API before starting file processing
    step("Attempting initial API authentication...")
    if not login():
        step("WARNING: Initial API authentication failed - will retry on first file processing")
        logging.warning("Initial API authentication failed, will retry during file processing")
    
    start_watcher(str(DUMP_FOLDER))
