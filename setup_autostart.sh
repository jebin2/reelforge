#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="tmux-startup"
SERVICE_DIR="$HOME/.config/systemd/user"

echo "Setting up $SERVICE_NAME systemd service..."

mkdir -p "$SERVICE_DIR"
cp "$SCRIPT_DIR/$SERVICE_NAME.service" "$SERVICE_DIR/"

systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME.service"
systemctl --user restart "$SERVICE_NAME.service"

loginctl enable-linger "$USER"

echo "Done. Status:"
systemctl --user status "$SERVICE_NAME.service" --no-pager
