#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PANELFLOW_DIR="$SCRIPT_DIR/../PanelFlow"
REELFORGE_DIR="$SCRIPT_DIR"

while true; do
    echo "[$(date)] Running reelforge..."
    cd "$REELFORGE_DIR" && bash run_app.sh --onepass

    echo "[$(date)] Running PanelFlow..."
    cd "$PANELFLOW_DIR" && bash run_app.sh --onepass

    echo "[$(date)] Sleeping for 60 seconds..."
    sleep 60
done
