#!/bin/bash
# wait_for.sh <regex in driver.events> <max seconds> : liveness-checked wait (driver pid must stay alive)
S=/home/makerspace/thesis_data/ablation; P=$(grep "DRIVER START" $S/driver.events | tail -1 | awk '{print $NF}')
t0=$(date +%s)
while true; do
  grep -qE "$1" $S/driver.events && { echo "MATCH: $(grep -E "$1" $S/driver.events | tail -1)"; exit 0; }
  kill -0 $P 2>/dev/null || { echo "DRIVER DEAD (pid $P)"; tail -3 $S/driver.events; exit 2; }
  [ $(( $(date +%s) - t0 )) -gt $2 ] && { echo "TIMEOUT after $2 s; last: $(tail -1 $S/timing.tsv)"; exit 1; }
  sleep 60
done
