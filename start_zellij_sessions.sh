#!/bin/bash
set -e

SESSION=content
LAYOUT="$HOME/git/reelforge/layouts/content.kdl"

if zellij list-sessions -s | grep -qx "$SESSION"; then
    zellij attach -f "$SESSION"
else
    echo "Creating session '$SESSION'..."
    script -qc "zellij attach -c -f $SESSION" /dev/null &
    sleep 5

    for i in 1 2 3 4 5; do
        zellij list-sessions -s | grep -qx "$SESSION" && break
        sleep 2
    done
fi

zellij --session "$SESSION" action write-chars "cd /home/ubuntu/git/reelforge && source venv/bin/activate && ./run_pipelines.sh"
zellij --session "$SESSION" action write 13

zellij --session "$SESSION" action focus-next-pane
zellij --session "$SESSION" action write-chars "cd /home/ubuntu/git/pub_yt_x && source venv/bin/activate && python main.py"
zellij --session "$SESSION" action write 13

zellij --session "$SESSION" action focus-next-pane
zellij --session "$SESSION" action write-chars "cd /home/ubuntu/git/solvechessdotcom && source venv/bin/activate && ./run_app.sh"
zellij --session "$SESSION" action write 13
