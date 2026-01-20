from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from processor import process_all_dumps
from pathlib import Path
import time
import logging
from steps import step


class DumpFileHandler(FileSystemEventHandler):
    def _maybe_process(self, src_path):
        if not src_path:
            return

        # ignore directories and hidden/temporary files
        p = Path(src_path)
        if p.is_dir() or p.name.startswith('.'):
            return

        if p.suffix.lower() == ".txt":
            step(f"System detected new dump file: {src_path}")
            # trigger processing loop which will process all files until empty
            process_all_dumps()

    def on_created(self, event):
        if event.is_directory:
            return
        logging.info(f"Event: created -> {getattr(event, 'src_path', None)}")
        self._maybe_process(event.src_path)

    def on_moved(self, event):
        # file moved into watched folder may fire as moved
        if event.is_directory:
            return
        logging.info(f"Event: moved -> dest={getattr(event, 'dest_path', None)} src={getattr(event, 'src_path', None)}")
        self._maybe_process(event.dest_path)

    def on_modified(self, event):
        # catch cases where a file is written in-place
        if event.is_directory:
            return
        logging.info(f"Event: modified -> {getattr(event, 'src_path', None)}")
        self._maybe_process(event.src_path)


def start_watcher(folder):
    folder_path = Path(folder)
    event_handler = DumpFileHandler()
    observer = Observer()
    observer.schedule(event_handler, str(folder_path), recursive=False)
    observer.start()

    step(f"Dump folder watcher started (watching: {folder_path})")

    # Process any existing .txt files present at startup
    try:
        for p in folder_path.iterdir():
            if p.is_file() and p.suffix.lower() == ".txt":
                step(f"System found existing dump file at startup: {p}")
                process_all_dumps()
    except Exception:
        logging.exception("Failed scanning existing files in dump folder")

    # Track seen files for polling fallback (handles WSL2 mount event miss)
    seen_files = set()
    try:
        # Initialize with existing files
        for p in folder_path.iterdir():
            if p.is_file() and p.suffix.lower() == ".txt" and not p.name.startswith('.'):
                seen_files.add(p.name)
    except Exception:
        pass

    try:
        while True:
            time.sleep(5)
            # Polling fallback for WSL2/mounted volumes where watchdog may miss events
            try:
                current_files = set()
                for p in folder_path.iterdir():
                    if p.is_file() and p.suffix.lower() == ".txt" and not p.name.startswith('.'):
                        current_files.add(p.name)
                
                # Check if new files appeared
                new_files = current_files - seen_files
                if new_files:
                    for fname in new_files:
                        step(f"Polling detected new dump file: {fname}")
                        logging.info(f"Polling detected new file (watchdog may have missed it): {fname}")
                    process_all_dumps()
                
                seen_files = current_files
            except Exception:
                logging.exception("Error in polling fallback")

    except KeyboardInterrupt:
        observer.stop()

    observer.join()
