#!/bin/bash

sleep 20

# Only create if not exists (prevents loops on restart)
tmux has-session -t reelforge 2>/dev/null || \
  tmux new-session -d -s reelforge \
    "bash -i -c 'cd $HOME/git/reelforge && penv && ./run_pipelines.sh; exec bash'"

tmux has-session -t publish 2>/dev/null || \
  tmux new-session -d -s publish \
    "bash -i -c 'cd $HOME/git/pub_yt_x && penv && python main.py; exec bash'"

tmux has-session -t chess 2>/dev/null || \
  tmux new-session -d -s chess \
    "bash -i -c 'cd $HOME/git/solvechessdotcom && penv && ./run_app.sh; exec bash'"
