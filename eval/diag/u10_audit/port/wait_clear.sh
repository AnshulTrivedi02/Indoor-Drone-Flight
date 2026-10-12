#!/bin/bash
# Wait until no flight runs: FLIGHT_LOCK absent AND no arducopter / gz sim process (exact comm names), polling every
# 60 s, giving up after $1 seconds (default 4 h). Prints CLEAR or TIMEOUT. Checks liveness every loop (no output wait).
LIMIT=${1:-14400}; T0=$(date +%s)
while true; do
  busy=""
  [ -e /home/makerspace/thesis_data/FLIGHT_LOCK ] && busy="FLIGHT_LOCK"
  pgrep -x arducopter > /dev/null && busy="$busy proc"
  pgrep -f '[g]z sim' > /dev/null && busy="$busy gz"
  if [ -z "$busy" ]; then echo "CLEAR $(date +%T)"; exit 0; fi
  if [ $(( $(date +%s) - T0 )) -gt $LIMIT ]; then echo "TIMEOUT $(date +%T): $busy"; exit 1; fi
  sleep 60
done
