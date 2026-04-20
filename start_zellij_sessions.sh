#!/bin/bash
set -e

SESSION=content
LAYOUT="$HOME/git/reelforge/layouts/content.kdl"

if zellij list-sessions -s | grep -qx "$SESSION"; then
    zellij attach -f "$SESSION" || true
else
    echo "Creating session '$SESSION'..."
    zellij -s "$SESSION" -l "$LAYOUT" &
    sleep 5
fi

if [ -z "$ZELLIJ_SESSION_NAME" ]; then
    echo "Not in zellij session. Run this from within zellij to send commands."
    echo "Script will send commands after you attach manually."
    exit 0
fi

zellij --session "$SESSION" action write-chars "cd /home/ubuntu/git/reelforge && source venv/bin/activate && ./run_pipelines.sh"
zellij --session "$SESSION" action write 13

zellij --session "$SESSION" action focus-next-pane
zellij --session "$SESSION" action write-chars "cd /home/ubuntu/git/pub_yt_x && source venv/bin/activate && python main.py"
zellij --session "$SESSION" action write 13

zellij --session "$SESSION" action focus-next-pane
zellij --session "$SESSION" action write-chars "cd /home/ubuntu/git/solvechessdotcom && source venv/bin/activate && ./run_app.sh"
zellij --session "$SESSION" action write 13
