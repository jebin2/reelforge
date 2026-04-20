#!/bin/bash
set -e

SESSION=content
LAYOUT="$HOME/git/reelforge/layouts/content.kdl"

if zellij list-sessions -s | grep -qx "$SESSION"; then
    zellij attach -f "$SESSION"
else
    zellij -s "$SESSION" -l "$LAYOUT"
    sleep 2
fi

zellij -s "$SESSION" write-chars "cd /home/ubuntu/git/reelforge && source venv/bin/activate && ./run_pipelines.sh"
zellij -s "$SESSION" write 13

zellij -s "$SESSION" focus-next-pane
zellij -s "$SESSION" write-chars "cd /home/ubuntu/git/pub_yt_x && source venv/bin/activate && python main.py"
zellij -s "$SESSION" write 13

zellij -s "$SESSION" focus-next-pane
zellij -s "$SESSION" write-chars "cd /home/ubuntu/git/solvechessdotcom && source venv/bin/activate && ./run_app.sh"
zellij -s "$SESSION" write 13
