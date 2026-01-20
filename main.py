import logging
from config import DUMP_FOLDER
from watcher import start_watcher
from steps import step, reset

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
    start_watcher(str(DUMP_FOLDER))
