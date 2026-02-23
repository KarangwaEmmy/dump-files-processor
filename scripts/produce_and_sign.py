#!/usr/bin/env python3
"""
Produce a dump file and its HMAC signature atomically.

Method:
 - Create a staging directory next to the target `out_dir`.
 - Write the dump file and its `.sig` into the staging dir.
 - Use `os.replace` to move both files into `out_dir` (atomic per-file rename on same filesystem).

Usage:
  python scripts/produce_and_sign.py --out-dir /mnt/c/Dump --name sample.txt --content "key=val" --secret s3cr3t
"""
import argparse
import tempfile
import os
import hashlib
import hmac
from pathlib import Path


def write_and_move_atomic(out_dir: Path, name: str, content: bytes, secret: str, sig_ext: str = '.sig'):
    out_dir = out_dir.resolve()
    # make staging dir as sibling to out_dir to ensure same filesystem
    parent = out_dir
    staging = parent / ('.staging_' + next(tempfile._get_candidate_names()))
    staging.mkdir(parents=True, exist_ok=False)
    try:
        tmp_file = staging / name
        tmp_sig = staging / (name + sig_ext)
        tmp_file.write_bytes(content)
        digest = hmac.new(secret.encode(), content, hashlib.sha256).hexdigest()
        tmp_sig.write_text(digest)

        final_file = out_dir / name
        final_sig = out_dir / (name + sig_ext)

        # atomic replace into destination (must be same filesystem)
        os.replace(tmp_file, final_file)
        os.replace(tmp_sig, final_sig)
        return final_file, final_sig
    finally:
        try:
            if staging.exists():
                staging.rmdir()
        except Exception:
            pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out-dir', required=True, help='Target dump directory')
    p.add_argument('--name', required=True, help='Filename to create (e.g., sample.txt)')
    p.add_argument('--content', default='', help='File content (or use --content-file)')
    p.add_argument('--content-file', help='Path to file to use as content')
    p.add_argument('--secret', required=True, help='HMAC secret')
    p.add_argument('--sig-ext', default='.sig', help='Signature extension')
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    if not out_dir.exists():
        raise SystemExit(f"out-dir does not exist: {out_dir}")

    if args.content_file:
        content = Path(args.content_file).read_bytes()
    else:
        content = args.content.encode()

    final_file, final_sig = write_and_move_atomic(out_dir, args.name, content, args.secret, args.sig_ext)
    print(f"Created {final_file} and {final_sig}")


if __name__ == '__main__':
    main()
