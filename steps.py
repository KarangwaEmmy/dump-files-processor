import logging
import threading

_lock = threading.Lock()
_run = 0
_counter = 0
_file_label = None
_file_counter = 0


def start_run():
    """Start a new step run. Subsequent `step(...)` calls will be numbered as `Run.Step`.

    Returns the run id (int).
    """
    global _run, _counter
    with _lock:
        _run += 1
        _counter = 0
        return _run


def step(message: str):
    """Log a numbered step message.

    If a run has been started via `start_run()`, messages are `Step {run}.{n}: ...`.
    Otherwise messages are `Step {n}: ...`.
    """
    global _counter, _run, _file_counter
    with _lock:
        run = _run
        if run and _file_label:
            _file_counter += 1
            n = _file_counter
            label = _file_label
            # emit per-file step
            logging.info(f"Step {run}.{label}.{n}: {message}")
            return

        # no file label active: use run-level or global counter
        _counter += 1
        n = _counter

    if run:
        logging.info(f"Step {run}.{n}: {message}")
    else:
        logging.info(f"Step {n}: {message}")


def reset():
    """Reset counters (testing/debug)."""
    global _run, _counter
    with _lock:
        _run = 0
        _counter = 0
        global _file_label, _file_counter
        _file_label = None
        _file_counter = 0


def start_file(label: str):
    """Start numbered steps for a specific file. Label should be a short identifier.

    Example: `start_file('a')` then `step(...)` -> `Step 1.a.1: ...`.
    """
    global _file_label, _file_counter
    with _lock:
        _file_label = str(label)
        _file_counter = 0


def end_file():
    """End the current file-scoped numbering."""
    global _file_label, _file_counter
    with _lock:
        _file_label = None
        _file_counter = 0
