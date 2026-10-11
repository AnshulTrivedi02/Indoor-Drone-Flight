#!/bin/bash
# rung-1 UKF port (2026-10-11): build Replay, UKF_Equiv and the copter SITL target from the scratch worktree of
# rung1-geometry + the working changes. Never installs; ~/ardupilot_ukf/build untouched.
set -e
W=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/apukf
cd $W
./waf configure --board sitl --no-submodule-update
./waf replay
./waf build --target examples/UKF_Equiv
./waf copter
md5sum build/sitl/tool/Replay build/sitl/examples/UKF_Equiv build/sitl/bin/*
