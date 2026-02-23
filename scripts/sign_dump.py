#!/usr/bin/env python3
"""
Sign dump files using HMAC-SHA256 and write sidecar .sig files.

Usage:
  # Sign a single file
  python scripts/sign_dump.py --file "C:\\Dump\\sample.txt" --secret s3cr3t

  # Sign all .txt files in a folder
  python scripts/sign_dump.py --folder "/mnt/c/Dump" --secret s3cr3t

The script writes a hex HMAC to the sidecar file `<filename>.sig` next to the input file.
"""
import argparse
import hashlib
import hmac
from pathlib import Path


def sign_file(path: Path, secret: str, sig_ext: str = '.sig'):
    with open(path, 'rb') as f:
        data = f.read()
    digest = hmac.new(secret.encode(), data, hashlib.sha256).hexdigest()
    sig_path = Path(str(path) + sig_ext)
    sig_path.write_text(digest)
    return sig_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--file', help='Single file to sign')
    p.add_argument('--folder', help='Folder containing files to sign (all .txt)')
    p.add_argument('--secret', required=True, help='HMAC secret')
    p.add_argument('--ext', default='.sig', help='Signature file extension (default: .sig)')
    p.add_argument('--print-only', action='store_true', help='Print HMAC to stdout instead of writing .sig file (useful for CI)')
    args = p.parse_args()

    if not args.file and not args.folder:
        p.error('Either --file or --folder is required')

    if args.file:
        path = Path(args.file)
        if not path.is_file():
            raise SystemExit(f"File not found: {path}")
        with open(path, 'rb') as f:
            data = f.read()
        digest = hmac.new(args.secret.encode(), data, hashlib.sha256).hexdigest()
        if args.print_only:
            print(digest)
        else:
            sig = sign_file(path, args.secret, args.ext)
            print(f"Wrote signature: {sig}")

    if args.folder:
        folder = Path(args.folder)
        if not folder.is_dir():
            raise SystemExit(f"Folder not found: {folder}")
        count = 0
        for f in sorted(folder.glob('*.txt')):
            with open(f, 'rb') as fh:
                data = fh.read()
            digest = hmac.new(args.secret.encode(), data, hashlib.sha256).hexdigest()
            if args.print_only:
                print(f"{f}: {digest}")
            else:
                sig = sign_file(f, args.secret, args.ext)
                print(f"Wrote signature: {sig}")
            count += 1
        print(f"Signed {count} files")


if __name__ == '__main__':
    main()
