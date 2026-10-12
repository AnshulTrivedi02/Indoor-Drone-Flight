#!/bin/bash
# A temporary detached worktree of the REBASED u4-gndclr, with the submodules a SITL Replay build needs, initialised by
# --reference to the main checkout (no network; the shared config is not edited).
set -e
MAIN=/home/makerspace/ardupilot_ukf
WT=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/g5a/u4wt
git -C $MAIN worktree add -q --detach $WT u4-gndclr
cd $WT
git rev-parse HEAD
for m in modules/waf modules/mavlink modules/DroneCAN/DSDL modules/DroneCAN/dronecan_dsdlc modules/DroneCAN/libcanard modules/DroneCAN/pydronecan modules/littlefs modules/lwip; do
  [ -e "$MAIN/$m/.git" ] || { echo "skip $m"; continue; }
  timeout 600 git submodule update --init --reference "$MAIN/$m" "$m" > /dev/null 2>&1 && echo "ok $m"
done
cd modules/mavlink
[ -e "$MAIN/modules/mavlink/pymavlink/.git" ] && timeout 600 git submodule update --init --reference "$MAIN/modules/mavlink/pymavlink" pymavlink > /dev/null 2>&1 && echo "ok pymavlink"
echo PREP_DONE
