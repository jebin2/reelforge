#!/bin/bash

sleep 20

SESSION_NAME="content"
LAYOUT_PATH="$HOME/git/reelforge/layouts/content.kdl"

if zellij list-sessions 2>/dev/null | grep -q "^${SESSION_NAME}$"; then
  exit 0
fi

zellij --new-session-with-layout "$LAYOUT_PATH" -s "$SESSION_NAME"