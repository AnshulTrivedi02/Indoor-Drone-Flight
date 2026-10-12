#!/bin/bash
# U10 rule 2 (2026-10-12): scratch SITL build of the replay-rukx worktree: Replay, UKF_Equiv, and the copter target as
# a compile check only (its binary is never installed). ~/ardupilot_ukf/build untouched. One heavy.py step.
set -e
W=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/apr
O=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/u10f/build
mkdir -p $O
cd $W
git rev-parse HEAD > $O/head.txt; git status --short >> $O/head.txt
./waf configure --board sitl --no-submodule-update > $O/configure.log 2>&1
./waf replay > $O/replay.log 2>&1
./waf build --target examples/UKF_Equiv > $O/equiv.log 2>&1
./waf copter > $O/copter.log 2>&1
md5sum build/sitl/tool/Replay build/sitl/examples/UKF_Equiv build/sitl/bin/* | tee $O/md5.txt
grep -c "warning:" $O/replay.log $O/equiv.log $O/copter.log || true
