#!/bin/bash
# 2026-10-12: install build of the merged ukf-jitter-fix (= rung1-geometry 16535f9a29): Replay and UKF_Equiv ONLY,
# in place in ~/ardupilot_ukf/build. The SITL vehicle binary is NOT rebuilt (no "waf copter"); its md5 is printed
# before and after to prove it unchanged.
set -e
cd /home/makerspace/ardupilot_ukf
git rev-parse HEAD
echo "before:"; md5sum build/sitl/tool/Replay build/sitl/examples/UKF_Equiv build/sitl/bin/*
./waf replay
./waf build --target examples/UKF_Equiv
echo "after:"; md5sum build/sitl/tool/Replay build/sitl/examples/UKF_Equiv build/sitl/bin/*
