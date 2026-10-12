#!/bin/bash
# XUKO FMT install (2026-10-12): ~/ardupilot_ukf on ukf-jitter-fix, fast-forwarded to xuko-fmt. Back up the installed
# Replay (be7c4d18) and UKF_Equiv (180cf2d8), then rebuild Replay and UKF_Equiv IN PLACE. The SITL copter binary is
# NOT rebuilt (no "waf copter"); its md5 is printed before and after. One heavy.py step.
set -e
cd /home/makerspace/ardupilot_ukf
git rev-parse HEAD; git branch --show-current; git status --short | head
B=/home/makerspace/opt/ukf_port_backup_be7c4d18_2026-10-12
mkdir -p $B
cp -p build/sitl/tool/Replay $B/Replay
cp -p build/sitl/examples/UKF_Equiv $B/UKF_Equiv
(cd $B && md5sum Replay UKF_Equiv > MD5SUMS && cat MD5SUMS)
echo "before:"; md5sum build/sitl/tool/Replay build/sitl/examples/UKF_Equiv build/sitl/bin/*
./waf replay
./waf build --target examples/UKF_Equiv
echo "after:"; md5sum build/sitl/tool/Replay build/sitl/examples/UKF_Equiv build/sitl/bin/*
