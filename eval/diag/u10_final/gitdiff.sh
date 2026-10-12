#!/bin/bash
cd /tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/apr
git status --short
git diff --stat
git diff | head -${1:-120}
