#!/bin/bash

sleep 20

# Only create if not exists (prevents loops on restart)
tmux has-session -t reelforge 2>/dev/null || \
  tmux new-session -d -s reelforge \
    "cd $HOME/git/reelforge && source ~/.bashrc && penv && ./run_pipelines.sh"

tmux has-session -t publish 2>/dev/null || \
  tmux new-session -d -s publish \
    "cd $HOME/git/reelforge && source ~/.bashrc && penv && ./run_app.sh --publisher"

tmux has-session -t chess 2>/dev/null || \
  tmux new-session -d -s chess \
    "cd $HOME/git/solvechessdotcom && source ~/.bashrc && penv && ./run_app.sh"
