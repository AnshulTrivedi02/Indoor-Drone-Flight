#!/bin/sh
# Copy the submodule WORKING TREES (no git metadata) from ~/ardupilot_ukf into the scratch worktree; build with
# --no-submodule-update. Read-only on ~/ardupilot_ukf.
set -e
DST=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/jfix/apukf/modules
for m in waf mavlink gtest DroneCAN Micro-XRCE-DDS-Client Micro-CDR lwip littlefs; do
  rsync -a --exclude=.git /home/makerspace/ardupilot_ukf/modules/$m/ $DST/$m/
done
ls $DST/waf | head -3
du -sh $DST
