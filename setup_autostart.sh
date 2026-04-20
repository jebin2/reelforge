#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="zellij-startup"
SERVICE_DIR="$HOME/.config/systemd/user"

echo "Setting up $SERVICE_NAME systemd service..."

mkdir -p "$SERVICE_DIR"

cat > "$SERVICE_DIR/$SERVICE_NAME.service" << 'EOF'
[Unit]
Description=Zellij Startup Sessions
After=network.target

[Service]
Type=oneshot
ExecStart=%h/git/reelforge/start_zellij_sessions.sh
RemainAfterExit=yes
Restart=on-failure
RestartSec=5

Environment=HOME=%h

KillMode=control-group

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME.service"
systemctl --user restart "$SERVICE_NAME.service"

loginctl enable-linger "$USER"

echo "Done. Status:"
systemctl --user status "$SERVICE_NAME.service" --no-pager