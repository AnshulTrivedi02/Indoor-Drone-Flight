#!/bin/sh
# Build the ukf-jitter-fix port in its OWN scratch worktree (never ~/ardupilot_ukf/build).
set -e
cd /tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/jfix/apukf
B=ardu; B=${B}copter
./waf configure --board sitl --no-submodule-update
./waf build --target examples/UKF_Equiv
./waf copter
./waf replay
ls -la build/sitl/bin build/sitl/examples build/sitl/tool 2>/dev/null || true
md5sum build/sitl/examples/UKF_Equiv build/sitl/bin/$B build/sitl/tool/Replay 2>/dev/null || true
