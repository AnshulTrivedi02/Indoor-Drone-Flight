#!/bin/bash
# when_clear.sh <limit_s> <script> [args]: poll every 5 s (FLIGHT_LOCK absent, no arducopter, no gz sim, no BUILD_LOCK),
# then run <script> at once (it re-checks itself). Gives up after <limit_s>. Liveness checked every loop.
LIMIT=$1; shift; T0=$(date +%s)
while true; do
  if [ ! -e /home/makerspace/thesis_data/FLIGHT_LOCK ] && [ ! -e /home/makerspace/thesis_data/BUILD_LOCK ] \
     && ! pgrep -x arducopter > /dev/null && ! pgrep -f '[g]z sim' > /dev/null; then
    echo "clear at $(date +%T)"; bash "$@"; rc=$?
    [ $rc = 3 ] || exit $rc            # 3 = the lock reappeared between the checks: keep waiting
  fi
  [ $(( $(date +%s) - T0 )) -gt $LIMIT ] && { echo "TIMEOUT $(date +%T)"; exit 9; }
  sleep 5
done
