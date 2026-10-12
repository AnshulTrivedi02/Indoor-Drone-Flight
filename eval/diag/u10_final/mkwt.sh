#!/bin/bash
# U10 rule 2 (2026-10-12): scratch worktree of ~/ardupilot_ukf on a NEW branch replay-rukx from ukf-jitter-fix.
set -e
WT=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/apr
cd /home/makerspace/ardupilot_ukf
git status --short | head
git worktree add -b replay-rukx "$WT" ukf-jitter-fix
cd "$WT"; git log --oneline -1
