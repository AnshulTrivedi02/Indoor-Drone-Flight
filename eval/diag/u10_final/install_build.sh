#!/bin/bash
# U10 rule 2 install (2026-10-12): ~/ardupilot_ukf on ukf-jitter-fix, fast-forwarded to replay-rukx. Back up the
# installed Replay (e82c050b) and UKF_Equiv (fe548d36), then rebuild Replay and UKF_Equiv IN PLACE. The SITL copter
# binary is NOT rebuilt (no "waf copter"); its md5 is printed before and after. One heavy.py step.
set -e
cd /home/makerspace/ardupilot_ukf
test "$(git branch --show-current)" = ukf-jitter-fix
test -z "$(git status --short)"
git merge --ff-only replay-rukx
git rev-parse HEAD; git log --oneline -2
B=/home/makerspace/opt/ukf_port_backup_e82c050b_2026-10-12
mkdir -p $B
cp -p build/sitl/tool/Replay $B/Replay
cp -p build/sitl/examples/UKF_Equiv $B/UKF_Equiv
(cd $B && md5sum Replay UKF_Equiv > MD5SUMS && cat MD5SUMS)
echo "before:"; md5sum build/sitl/tool/Replay build/sitl/examples/UKF_Equiv build/sitl/bin/*
./waf replay
./waf build --target examples/UKF_Equiv
echo "after:"; md5sum build/sitl/tool/Replay build/sitl/examples/UKF_Equiv build/sitl/bin/*
