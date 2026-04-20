#!/bin/bash

SESSION=content
LAYOUT="$HOME/git/reelforge/layouts/content.kdl"

if zellij list-sessions -s | grep -qx "$SESSION"; then
    zellij attach -f "$SESSION"
else
    zellij -s "$SESSION" -l "$LAYOUT"
fi
