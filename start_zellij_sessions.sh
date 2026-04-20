#!/bin/bash

set -e

sleep 20

ZELLIJ_DIR="$HOME/.local/bin"
export PATH="$ZELLIJ_DIR:$PATH"

if ! command -v zellij &> /dev/null; then
  echo "Installing zellij..."
  mkdir -p "$ZELLIJ_DIR"
  cd "$ZELLIJ_DIR"
  curl -fSL https://github.com/zellij-org/zellij/releases/latest/download/zellij-x86_64-unknown-linux-musl.tar.gz -o zellij.tar.gz
  tar -xzf zellij.tar.gz
  chmod +x zellij
  mv zellij "$ZELLIJ_DIR/"
  rm -f zellij.tar.gz
  cd - > /dev/null
fi

SESSION_NAME="content"

if zellij list-sessions 2>/dev/null | grep -q "^${SESSION_NAME}$"; then
  echo "Session already running"
  exit 0
fi

LAYOUT_PATH="$HOME/git/reelforge/layouts/content.kdl"
echo "Starting zellij session..."

nohup zellij -s "$SESSION_NAME" --new-session-with-layout "$LAYOUT_PATH" > /tmp/zellij.log 2>&1 &
sleep 3