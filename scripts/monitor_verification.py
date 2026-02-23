#!/usr/bin/env python3
"""
Monitor verification state and logs and send alerts for tamper detection.

Runs as a one-shot tool (cron/systemd timer) or can be looped.

Behavior:
 - Read `STATE_FILE` and send alert for any file with count >= ALERT_THRESHOLD.
 - Read recent lines from `VERIFICATION_LOG` and summarize recent invalid/error events and send one alert.
 - Optionally compare current hashes against a baseline JSON (path passed with --baseline) and alert on mismatches.
"""
import time
import json
from pathlib import Path
from config import STATE_FILE, VERIFICATION_LOG, ALERT_THRESHOLD
from scripts.notifier import send_alert
import argparse


def read_state():
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def read_recent_verification(interval_seconds=3600):
    if not VERIFICATION_LOG.exists():
        return []
    now = time.time()
    out = []
    try:
        with open(VERIFICATION_LOG, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                except Exception:
                    continue
                if now - obj.get('timestamp', 0) <= interval_seconds:
                    out.append(obj)
    except Exception:
        pass
    return out


def compare_baseline(baseline_path):
    try:
        baseline = json.loads(Path(baseline_path).read_text())
    except Exception:
        return {}
    current = {}
    # baseline format: {"/path/to/file": {"sha256": "...", ...}}
    for p, info in baseline.items():
        current[p] = info.get('sha256')
    # attempt to read actual files and compute sha256
    mismatches = {}
    import hashlib
    for p, expected in current.items():
        try:
            b = Path(p).read_bytes()
            h = hashlib.sha256(b).hexdigest()
            if h != expected:
                mismatches[p] = {'expected': expected, 'found': h}
        except Exception:
            mismatches[p] = {'error': 'file missing or unreadable'}
    return mismatches


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', help='Optional baseline JSON to compare')
    parser.add_argument('--recent-seconds', type=int, default=3600, help='Window for summarizing recent verification events')
    args = parser.parse_args()

    state = read_state()
    for path, cnt in state.items():
        if cnt >= ALERT_THRESHOLD:
            alert = {'subject': 'Repeated verification failures', 'file': path, 'count': cnt}
            send_alert(alert)

    recent = read_recent_verification(args.recent_seconds)
    invalids = [r for r in recent if r.get('result') in ('invalid', 'error')]
    if invalids:
        summary = {'subject': 'Recent invalid verification events', 'count': len(invalids), 'events': invalids}
        send_alert(summary)

    if args.baseline:
        mismatches = compare_baseline(args.baseline)
        if mismatches:
            alert = {'subject': 'Baseline mismatches detected', 'mismatches': mismatches}
            send_alert(alert)


if __name__ == '__main__':
    main()
