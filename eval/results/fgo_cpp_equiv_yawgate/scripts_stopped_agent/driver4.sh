#!/bin/bash
# after driver3: re-run fi60 with the checkpoint fix (fgo_chain now evaluated at the last keyframe)
Y=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/yawgate
end=$(( $(date +%s) + 5400 ))
while pgrep -f "yawgate/driver3.sh" >/dev/null && [ $(date +%s) -lt $end ]; do sleep 20; done
cp $Y/fi60.json $Y/fi60_wrongchk.json
python3 $HOME/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py --wait-s 3600 "yawgate fi60 rerun" -- bash $Y/step2.sh fi60 > $Y/logs/fi60b.log 2>&1
echo "fi60b rc $?"
