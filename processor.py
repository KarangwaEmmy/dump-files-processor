from pathlib import Path
import logging
import os
import time
import shutil
from api_client import send_to_api
from steps import step, start_file, end_file
from maha_mapping import MAHA_CODE_MAPPING
from config import DUMP_FOLDER, PROCESSED_FOLDER


LOCK_NAME = ".processing.lock"


def parse_key_value_file(file_path):
    data = {}

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()

            # Ignore comments and empty lines
            if not line or line.startswith(";") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()

    return data


def _acquire_lock():
    lock_path = Path(DUMP_FOLDER) / LOCK_NAME
    try:
        # atomic create
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        return fd
    except FileExistsError:
        # existing lock file - check if process is still running
        try:
            content = lock_path.read_text()
            pid = int(content.strip())
        except Exception:
            # can't read pid; assume stale and remove
            try:
                lock_path.unlink()
            except Exception:
                pass
            return None

        try:
            # check process exists (0 -> no signal, just check)
            os.kill(pid, 0)
            # process exists -> another instance running
            return None
        except OSError:
            # process does not exist -> stale lock, remove and retry creating
            try:
                lock_path.unlink()
            except Exception:
                pass
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                return fd
            except Exception:
                return None
    except Exception:
        logging.exception("Unable to acquire processing lock")
        return None


def _release_lock(fd):
    try:
        lock_path = Path(DUMP_FOLDER) / LOCK_NAME
        os.close(fd)
        if lock_path.exists():
            lock_path.unlink()
    except Exception:
        logging.exception("Failed to release processing lock")


def _move_to_processed(src_path, reason=None):
    src = Path(src_path)
    dest = PROCESSED_FOLDER / src.name
    try:
        dest_parent = dest.parent
        dest_parent.mkdir(parents=True, exist_ok=True)
        try:
            src.rename(dest)
        except OSError:
            # fallback across filesystems
            shutil.move(str(src), str(dest))
    except Exception:
        logging.exception(f"Failed to move {src_path} to processed folder")


def _process_single(file_path):
    try:
        step(f"Processing file: {file_path}")

        data = parse_key_value_file(file_path)

        # Build structured payload for API using known MAHA codes
        # basic metadata
        plate = data.get("10100")
        manufacturer = data.get("10201") or data.get("10200")
        vehicle_type = data.get("10200")
        axle_count = data.get("10190")
        chassis_no = data.get("10192")
        inspector_name = data.get("10512")
        lane_number = data.get("10010")
        inspection_date_raw = data.get("10107")
        inspection_time_raw = data.get("10131")

        # inspectionReference: MAHA-<date>-<time> (fall back to timestamp)
        ref_date = inspection_date_raw or time.strftime("%Y%m%d")
        ref_time = inspection_time_raw or time.strftime("%H%M%S")
        inspection_ref = f"MAHA-{ref_date}-{ref_time}".replace(':', '')

        # try to create ISO datetime for inspectionDate
        try:
            # attempt common formats: YYYYMMDD and HH:MM or HHMMSS
            if inspection_date_raw and len(inspection_date_raw) == 8:
                y = inspection_date_raw[0:4]
                m = inspection_date_raw[4:6]
                d = inspection_date_raw[6:8]
                if inspection_time_raw:
                    t = inspection_time_raw.replace(':', '')
                    if len(t) <= 4:
                        hh = t[0:2]
                        mm = t[2:4] if len(t) >= 4 else '00'
                        ss = '00'
                    else:
                        hh = t[0:2]
                        mm = t[2:4]
                        ss = t[4:6] if len(t) >= 6 else '00'
                    inspection_iso = f"{y}-{m}-{d}T{hh}:{mm}:{ss}Z"
                else:
                    inspection_iso = f"{y}-{m}-{d}T00:00:00Z"
            else:
                inspection_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            inspection_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ")

        payload = {
            "inspectionReference": inspection_ref,
            "inspectionDate": inspection_iso,
            "source": "MAHA",
            "inspectorName": inspector_name or "Unknown",
            "inspectionTime": inspection_time_raw or "",
            "plateNumber": plate,
            "ChassisNo": chassis_no,
            "manufacturer": manufacturer,
            "vehicleYype": vehicle_type,
            "axleCount": int(axle_count) if axle_count and axle_count.isdigit() else axle_count,
            "laneNumber": lane_number,
            "overallResult": "PASS",
            "inspectionResults": []
        }

        # populate inspectionResults from available codes
        for code, meta in MAHA_CODE_MAPPING.items():
            if code in data and data[code] not in (None, ""):
                raw = data[code]
                # try numeric conversion
                value = raw
                try:
                    if '.' in raw:
                        value = float(raw)
                    else:
                        value = int(raw)
                except Exception:
                    # keep as string
                    value = raw

                payload["inspectionResults"].append({
                    "code": code,
                    "value": value,
                    "testCategory": meta.get("category")
                })

        step(f"Built payload with {len(payload['inspectionResults'])} results")

        # Try sending to API with retries; only move file on success
        max_attempts = 3
        attempt = 0
        sent = False
        while attempt < max_attempts and not sent:
            attempt += 1
            try:
                sent = send_to_api(payload)
                if not sent:
                    step(f"Attempt {attempt}: send_to_api returned False")
            except Exception:
                logging.exception(f"send_to_api raised exception on attempt {attempt}")
                sent = False

            if not sent and attempt < max_attempts:
                time.sleep(1)

        if sent:
            # Move file to processed folder
            _move_to_processed(file_path)
            step(f"Processing completed successfully: {file_path}")
            return True
        else:
            step(f"Failed to send data to API after {max_attempts} attempts: {file_path}")
            # fallthrough to failure handling below

    except Exception as e:
        step(f"Failed to process {file_path}: {e}")
        # move failed files to processed with .failed suffix to avoid blocking
        try:
            failed_name = Path(file_path).name + ".failed"
            dest = PROCESSED_FOLDER / failed_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                Path(file_path).rename(dest)
            except OSError:
                shutil.move(str(file_path), str(dest))
        except Exception:
            logging.exception("Failed to move failed file to processed folder")
        return False
    finally:
        # ensure per-file numbering is cleared
        end_file()


def process_all_dumps():
    """Process all .txt files in the dump folder sequentially until empty.

    Uses a lock file to avoid concurrent runs.
    """
    from steps import start_run

    # begin a new numbered run for this processing invocation
    start_run()

    fd = _acquire_lock()
    if fd is None:
        logging.info("Another processing instance is running; skipping this run.")
        return

    try:
        dump_dir = Path(DUMP_FOLDER)
        while True:
            try:
                files = [p for p in dump_dir.iterdir()
                         if p.is_file() and p.suffix.lower() == ".txt"]
            except Exception:
                logging.exception("Failed to list dump folder")
                break

            if not files:
                break

            # sort by modification time to process oldest first
            files.sort(key=lambda p: p.stat().st_mtime)

            for p in files:
                # label files by index within this run: 1,2,3...
                idx = files.index(p) + 1
                start_file(str(idx))
                _process_single(str(p))

            # small pause to allow other writers to finish
            time.sleep(0.1)

    finally:
        _release_lock(fd)
