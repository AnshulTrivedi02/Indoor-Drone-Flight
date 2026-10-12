#!/bin/bash
# ONE heavy step (run under heavy.py): SITL Replay build of the rebased u4-gndclr worktree. Never installs.
set -e
WT=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/g5a/u4wt
O=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/g5a/u4build
mkdir -p $O
cd $WT
git rev-parse HEAD > $O/head.txt; git status --short >> $O/head.txt
./waf configure --board sitl --no-submodule-update > $O/configure.log 2>&1
./waf replay > $O/replay_build.log 2>&1
md5sum build/sitl/tool/Replay | tee $O/md5.txt
echo "warnings: $(grep -c 'warning:' $O/replay_build.log || true)"
