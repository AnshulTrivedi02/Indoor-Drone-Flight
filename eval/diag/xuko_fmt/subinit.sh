#!/bin/bash
# XUKO FMT (2026-10-12): init the submodules a SITL build needs in the scratch worktree, by --reference to the main
# checkout (no network fetch). Same as port_merge_u4/u4_subinit.sh with the new path.
set -e
WT=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/apx
MAIN=/home/makerspace/ardupilot_ukf
cd "$WT"
for m in modules/waf modules/mavlink modules/DroneCAN/DSDL modules/DroneCAN/dronecan_dsdlc modules/DroneCAN/libcanard modules/DroneCAN/pydronecan modules/littlefs modules/lwip; do
  echo "== $m"
  if [ ! -e "$MAIN/$m/.git" ]; then echo "  not initialised in main checkout, skipped"; continue; fi
  timeout 600 git submodule update --init --reference "$MAIN/$m" "$m" 2>&1 | tail -2
done
cd modules/mavlink
if [ -e "$MAIN/modules/mavlink/pymavlink/.git" ]; then
  timeout 600 git submodule update --init --reference "$MAIN/modules/mavlink/pymavlink" pymavlink 2>&1 | tail -2
fi
cd "$WT"
git submodule status --recursive | grep -v '^-'
