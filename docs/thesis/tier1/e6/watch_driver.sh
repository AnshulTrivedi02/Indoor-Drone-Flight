#!/usr/bin/env bash
# watch_driver.sh <driver log> <done file> <driver pgrep pattern> : emit new END lines; exit on done or driver death
L=$1; DONE=$2; PAT=$3
n=$(grep -c END "$L" 2>/dev/null || echo 0)
while true; do
  m=$(grep -c END "$L" 2>/dev/null || echo 0)
  if [ "$m" -gt "$n" ]; then grep END "$L" | tail -n $((m - n)); n=$m; fi
  [ -e "$DONE" ] && { echo DONE; exit 0; }
  pgrep -f "$PAT" >/dev/null || { echo "DRIVER GONE"; exit 1; }
  sleep 20
done
