# Pushing to GitHub — PAT and SSH setup

This short README shows exact steps to:
- Add a GitHub Personal Access Token (PAT) for HTTPS pushes, or
- Generate an SSH key and add it to GitHub, then push using SSH.

Use the method you prefer. SSH is recommended long-term.

---

1) Verify current remote (shows current config)

```bash
cd /home/ekarangw/dump_listener
git remote -v
```

2) Switch remote to SSH (already executed here)

```bash
git remote set-url origin git@github.com:KarangwaEmmy/dump-files-processor.git
git remote -v
```

3) SSH method (recommended)

- Generate an SSH key (if you don't have one):

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# Accept default path (~/.ssh/id_ed25519) and optionally set a passphrase
```

- Start the ssh-agent and add your key:

```bash
# Linux / macOS
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Windows (PowerShell)
# Start-Service ssh-agent
# ssh-add $env:USERPROFILE\.ssh\id_ed25519
```

- Copy the public key and add it to GitHub:

```bash
cat ~/.ssh/id_ed25519.pub
# Copy the output and add it to https://github.com/settings/ssh/new
```

- Test the SSH connection:

```bash
ssh -T git@github.com
# You should see: "Hi <username>! You've successfully authenticated..."
```

- Push the `verification` branch (create it locally if needed):

```bash
# create branch if it doesn't exist
git branch --list verification || git checkout -b verification
# push to GitHub
git push origin verification --set-upstream
```

4) PAT (HTTPS) method (quick, less secure if token stored in URL)

- Create a PAT on GitHub: https://github.com/settings/tokens
  - Click "Generate new token (classic)" or the new fine-grained token flow
  - Give it `repo` scope (or select appropriate scopes)
  - Copy the token once; you won't see it again

- Configure credential helper (Windows example):

```powershell
# Windows: use GCM (Git Credential Manager)
git config --global credential.helper manager-core
```

- Push using HTTPS (you'll be prompted for username and token as password):

```bash
# set remote to HTTPS (if you need to)
git remote set-url origin https://github.com/KarangwaEmmy/dump-files-processor.git
# push
git push origin verification --set-upstream
# When asked for password, paste the PAT
```

- (Optional) embed PAT in remote URL — NOT RECOMMENDED for security:

```bash
# WARNING: token in URL is visible in shell history
git remote set-url origin https://<username>:<PAT>@github.com/KarangwaEmmy/dump-files-processor.git
git push origin verification --set-upstream
```

---

5) Troubleshooting

- `Permission denied (publickey)`: SSH key not added to GitHub or agent not running.
- `remote: Repository not found`: check you have access to the repository and the URL is correct.
- `fatal: Authentication failed`: PAT not provided or invalid; try re-creating token.

---

If you'd like, I can attempt the push here once you confirm SSH is added to your GitHub account (or you provide a PAT). Otherwise, run the commands above locally and send the push output if you want me to verify further.