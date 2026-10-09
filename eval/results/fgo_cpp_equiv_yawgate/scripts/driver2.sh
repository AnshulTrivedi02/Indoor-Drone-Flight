#!/bin/bash
# POST-HOC forced-gate diagnostics after driver.sh (each via heavy.py). Usage: driver2.sh <name:prefix:script:args>...
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad
Y=$S/yawgate2
HEAVY="python3 $HOME/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py"
end=$(( $(date +%s) + 7200 ))
while pgrep -f "yawgate2/driver.sh" >/dev/null && [ $(date +%s) -lt $end ]; do sleep 20; done
for spec in "$@"; do
  IFS=: read -r mode name p script args <<< "$spec"
  left=$(( end - $(date +%s) )); [ $left -le 60 ] && { echo "[driver2] SKIP $name"; continue; }
  echo "[driver2] $(date +%T) START $name"
  $HEAVY --wait-s $left "yawgate2 $name" -- bash $Y/step2.sh $mode $p $script $args > $Y/logs/$name.log 2>&1
  echo "[driver2] $(date +%T) END $name rc=$?"
done
echo "[driver2] $(date +%T) ALL DONE"
