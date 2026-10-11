#!/bin/bash
# board-h743 (2a, 2026-10-11): SITL rebuild of the board-h743 working tree (Replay, UKF_Equiv, the copter SITL binary),
# for the byte-identity proof. Never installs; ~/ardupilot_ukf/build untouched. One heavy.py step.
set -e
W=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/aph7
O=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/h7/out/sitl
mkdir -p $O
cd $W
./waf configure --board sitl --no-submodule-update > $O/configure.log 2>&1
./waf replay > $O/replay.log 2>&1
./waf build --target examples/UKF_Equiv > $O/equiv.log 2>&1
./waf copter > $O/copter.log 2>&1
md5sum build/sitl/tool/Replay build/sitl/examples/UKF_Equiv build/sitl/bin/* | tee $O/md5.txt
grep -c "warning:" $O/replay.log $O/equiv.log $O/copter.log || true
