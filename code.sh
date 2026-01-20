sudo tee /etc/systemd/system/dump_listener.service > /dev/null <<'UNIT'
[Unit]
Description=Dump Listener
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/repo
Environment=DUMP_DIR=/path/to/Dump
ExecStart=/usr/bin/python3 /path/to/repo/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now dump_listener.service



HOW to RUN:
sudo docker-compose logs -f dump_listener
sudo docker exec -it dump_listener ls -la /app/Dump /app/Dump/processed