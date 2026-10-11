#!/bin/bash
# board-h743 stage: init the submodules a SITL + ChibiOS build needs, referencing the main checkout (no network fetch).
set -e
WT=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/aph7
MAIN=/home/makerspace/ardupilot_ukf
cd "$WT"
for m in modules/waf modules/mavlink modules/ChibiOS modules/DroneCAN/DSDL modules/DroneCAN/dronecan_dsdlc modules/DroneCAN/libcanard modules/DroneCAN/pydronecan modules/littlefs modules/lwip modules/CrashDebug; do
  echo "== $m"
  if [ ! -e "$MAIN/$m/.git" ]; then echo "  not initialised in main checkout, skipped"; continue; fi
  timeout 600 git submodule update --init --reference "$MAIN/$m" "$m" 2>&1 | tail -2
done
git submodule status | grep -v '^-'
