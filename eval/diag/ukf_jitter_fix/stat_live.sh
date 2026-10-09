#!/bin/sh
# Fingerprint the main session's ~/ardupilot_ukf build state (must be unchanged by this stage).
B=ardu; B=${B}copter
R=/home/makerspace/ardupilot_ukf
md5sum $R/.lock-waf_linux_build
stat -c '%y %n' $R/build/sitl/bin/$B $R/build/sitl/examples/UKF_Equiv $R/build/sitl/tool/Replay $R/build/c4che/_cache.py
md5sum $R/build/sitl/bin/$B $R/build/sitl/examples/UKF_Equiv $R/build/sitl/tool/Replay
git -C $R branch --show-current
git -C $R status --short | head
