#!/usr/bin/env bash
# FGO ground test (METHODOLOGY "FGO ground test ... DEVIATION"): once fly_trial reports the armed hold, wait
# DELAY wall seconds, then SIGINT the FGO node (FG2 node-stop test). Usage: node_stop_watch.sh TRIAL DELAY_S
T="$HOME/thesis_data/trials/$1/logs/fly_trial.log"; D="$2"; L=$((SECONDS+900))
until grep -q "GROUND_TEST: holding" "$T" 2>/dev/null || [ $SECONDS -gt $L ]; do sleep 1; done
grep -q "GROUND_TEST: holding" "$T" 2>/dev/null || { echo "no hold seen"; exit 1; }
echo "hold seen at $(date +%T); stopping the node in ${D}s"; sleep "$D"
pkill -INT -f "estimators/fgo/fgo_node[.]py" && echo "node SIGINT at $(date +%T)"
