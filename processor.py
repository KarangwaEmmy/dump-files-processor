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


def _move_to_appointment(src_path, reason=None):
    """Move file to Appointment folder with timestamp_filename format.
    
    Example: 2026-01-22_10-30-45_test_vehicle.txt
    """
    src = Path(src_path)
    appointment_folder = DUMP_FOLDER / "Appointment"
    
    try:
        appointment_folder.mkdir(parents=True, exist_ok=True)
        
        # Create timestamp_filename format: YYYY-MM-DD_HH-MM-SS_originalname.txt
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        dest_name = f"{timestamp}_{src.stem}.txt"
        dest = appointment_folder / dest_name
        
        try:
            src.rename(dest)
        except OSError:
            # fallback across filesystems
            shutil.move(str(src), str(dest))
        
        step(f"File moved to Appointment folder: {dest_name}")
        logging.info(f"File moved to Appointment folder: {dest}")
    except Exception:
        logging.exception(f"Failed to move {src_path} to Appointment folder")


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

        # try to create ISO datetime for inspectionDate (ISO 8601 with timezone)
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
                    inspection_iso = f"{y}-{m}-{d}T{hh}:{mm}:{ss}.000Z"
                else:
                    inspection_iso = f"{y}-{m}-{d}T00:00:00.000Z"
            else:
                inspection_iso = time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        except Exception:
            inspection_iso = time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        # Try to convert chassis number to integer (handles decimal strings like "0.000")
        try:
            chassis_no_value = int(float(chassis_no)) if chassis_no else 0
        except (ValueError, TypeError):
            chassis_no_value = 0

        payload = {
            "inspectionReference": inspection_ref,
            "inspectionDate": inspection_iso,
            "source": "MAHA",
            "inspectorName": inspector_name or "Unknown",
            "inspectionTime": inspection_time_raw or "",
            "plateNumber": plate,
            "chassisNo": chassis_no_value,
            "manufacturer": manufacturer,
            "vehicleType": vehicle_type,
            "axleCount": int(float(axle_count)) if axle_count else None,
            "laneNumber": str(lane_number) if lane_number else "",
            "overallResult": "PASS",
            "inspectionResults": []
        }

        # populate inspectionResults from available codes
        # EXCLUDE Vehicle Identification codes (those are in top-level fields)
        for code, meta in MAHA_CODE_MAPPING.items():
            # Skip Vehicle Identification category - those are already in payload top-level fields
            if meta.get("category") == "Vehicle Identification":
                continue
                
            if code in data and data[code] not in (None, ""):
                raw = data[code]
                # try numeric conversion, skip if not numeric
                value = None
                try:
                    if '.' in str(raw):
                        value = float(raw)
                    else:
                        value = int(raw)
                except (ValueError, TypeError):
                    # Skip non-numeric values - API expects integer
                    continue

                payload["inspectionResults"].append({
                    "code": code,
                    "value": value,
                    "testCategory": meta.get("category")
                })

        step(f"Built payload with {len(payload['inspectionResults'])} results")

        # Try sending to API with retries; only move file on success
        max_attempts = 3
        attempt = 0
        api_result = None
        while attempt < max_attempts and api_result is None:
            attempt += 1
            try:
                # send_to_api now returns (success, response_text)
                api_result = send_to_api(payload)
                if not api_result[0]:  # Check if success flag is False
                    step(f"Attempt {attempt}: API returned error - {api_result[1][:100]}")
            except Exception:
                logging.exception(f"send_to_api raised exception on attempt {attempt}")
                api_result = None

            if api_result is None and attempt < max_attempts:
                time.sleep(1)

        if api_result and api_result[0]:
            # Success - move file to processed folder
            _move_to_processed(file_path)
            step(f"Processing completed successfully: {file_path}")
            return True
        elif api_result:
            # API returned an error - check if it's an appointment error
            response_text = api_result[1]
            if "No validated appointment found for plate number" in response_text:
                step(f"Appointment validation error - moving to Appointment folder")
                _move_to_appointment(file_path)
                logging.warning(f"Appointment error for file {file_path}: {response_text}")
                return True  # Treat as handled success (file moved to Appointment folder)
            else:
                step(f"Failed to send data to API after {max_attempts} attempts: {file_path}")
                # Fallthrough to generic failure handling
        else:
            step(f"Failed to send data to API after {max_attempts} attempts: {file_path}")

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
