#!/usr/bin/env python3
"""
Scan a Dump folder for verification codes and compute file identity (hash + metadata).

Usage examples:
  python scripts/scan_dump.py --path "C:\\Dump" --codes 51381,51380,51387,51386,RAA520P
  python scripts/scan_dump.py --path /mnt/c/Dump --save-baseline baseline.json
"""
import argparse
import os
import hashlib
import json
import time
import re
from pathlib import Path


def file_hashes(path):
    h256 = hashlib.sha256()
    h1 = hashlib.sha1()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(8192), b''):
            h256.update(b)
            h1.update(b)
    return h256.hexdigest(), h1.hexdigest()


def scan_folder(folder, codes):
    out = {}
    folder = Path(folder)
    if not folder.exists():
        raise FileNotFoundError(folder)
    for p in sorted(folder.iterdir()):
        if not p.is_file():
            continue
        try:
            s = p.stat()
            sha256, sha1 = file_hashes(p)
            text = ''
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            except Exception:
                text = ''
            found = [c for c in codes if re.search(rf"\b{re.escape(c)}\b", text)]
            ts_like = re.findall(r'20\d{6}\s*\d{6,9}|20\d{10,12}', text)
            out[str(p)] = {
                'sha256': sha256,
                'sha1': sha1,
                'size': s.st_size,
                'mtime': s.st_mtime,
                'ctime': s.st_ctime,
                'found_codes': found,
                'ts_like': ts_like,
            }
        except Exception as e:
            out[str(p)] = {'error': str(e)}
    return out


def compare_baseline(report, baseline):
    diffs = {}
    for path, info in report.items():
        if path not in baseline:
            diffs[path] = {'status': 'new', 'info': info}
            continue
        b = baseline[path]
        if info.get('sha256') != b.get('sha256'):
            diffs[path] = {'status': 'modified', 'before': b.get('sha256'), 'after': info.get('sha256')}
    for path in baseline:
        if path not in report:
            diffs[path] = {'status': 'missing'}
    return diffs


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--path', '-p', required=True, help='Dump folder path')
    p.add_argument('--codes', '-c', default='', help='Comma separated codes to look for')
    p.add_argument('--save-baseline', help='Write report JSON to this file')
    p.add_argument('--compare-baseline', help='Compare against an existing baseline JSON')
    args = p.parse_args()

    codes = [x.strip() for x in args.codes.split(',') if x.strip()] if args.codes else []
    report = scan_folder(args.path, codes)
    print(json.dumps(report, indent=2))

    if args.save_baseline:
        with open(args.save_baseline, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"Saved baseline to {args.save_baseline}")

    if args.compare_baseline:
        with open(args.compare_baseline, 'r', encoding='utf-8') as f:
            baseline = json.load(f)
        diffs = compare_baseline(report, baseline)
        print('\nDifferences compared to baseline:')
        print(json.dumps(diffs, indent=2))


if __name__ == '__main__':
    main()
