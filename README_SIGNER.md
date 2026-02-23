Signer script

Use `scripts/sign_dump.py` to create HMAC-SHA256 .sig sidecar files for dump producers.

Examples:

# Sign a single file
python3 scripts/sign_dump.py --file "C:\\Dump\\sample.txt" --secret s3cr3t

# Sign all .txt files in a folder (WSL path)
python3 scripts/sign_dump.py --folder /mnt/c/Dump --secret s3cr3t

Notes:
- The script writes a hex HMAC into `<file>.sig`.
- `processor.py` expects sidecar files named like `file.txt.sig` or `file.txt.hmac`.
