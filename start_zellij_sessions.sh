#!/bin/bash

SESSION=content
LAYOUT="$HOME/git/reelforge/layouts/content.kdl"

ACTIVE=$(zellij list-sessions -s 2>/dev/null || true)

if echo "$ACTIVE" | grep -qx "$SESSION"; then
    zellij attach -f "$SESSION"
elif [ -z "$ACTIVE" ]; then
    echo "No sessions. Creating new one..."
    script -qc "zellij -s $SESSION -l $LAYOUT" /dev/null 2>/dev/null &
    sleep 5
else
    echo "Available: $ACTIVE"
    echo "Session '$SESSION' not found. Create manually then re-run."
fi
