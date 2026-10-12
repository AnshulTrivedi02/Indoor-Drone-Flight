#!/bin/bash
# Remove the scratch port worktree (the branch replay-rukx is kept); show the port checkout's final state.
cd /home/makerspace/ardupilot_ukf
git worktree remove --force /tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/apr
git worktree prune
git worktree list
git branch --show-current; git status --short | head; git log --oneline -1
git branch --contains f30f6ffa2f
