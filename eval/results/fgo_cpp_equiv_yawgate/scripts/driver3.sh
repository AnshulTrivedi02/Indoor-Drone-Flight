#!/bin/bash
# after driver.sh and driver2.sh: the acceptance dry run (via heavy.py); bounded wait
Y=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/yawgate2
end=$(( $(date +%s) + 9000 ))
while { pgrep -f yawgate2/driver.sh >/dev/null || pgrep -f yawgate2/driver2.sh >/dev/null; } && [ $(date +%s) -lt $end ]; do sleep 20; done
python3 /home/makerspace/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py --wait-s 3600 "yawgate2 acceptance dry run" -- bash $Y/accept.sh > $Y/logs/accept.log 2>&1
echo "[driver3] accept rc $?"
