#!/bin/bash

sleep 20

if ! command -v zellij &> /dev/null; then
  echo "Installing zellij..."
  curl -LO https://github.com/zellij-org/zellij/releases/latest/download/zellij-x86_64-unknown-linux-musl.tar.gz
  tar -xvf zellij-x86_64-unknown-linux-musl.tar.gz
  chmod +x zellij
  mv zellij "$HOME/.local/bin/"
  rm -f zellij-x86_64-unknown-linux-musl.tar.gz
fi

SESSION_NAME="content"
LAYOUT_PATH="$HOME/git/reelforge/layouts/content.kdl"

if zellij list-sessions 2>/dev/null | grep -q "^${SESSION_NAME}$"; then
  exit 0
fi

zellij --new-session-with-layout "$LAYOUT_PATH" -s "$SESSION_NAME"