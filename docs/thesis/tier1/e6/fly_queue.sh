#!/usr/bin/env bash
# fly_queue.sh <profile> <trial> [<trial> ...]: for each trial, wait (cap 2 h) until no plot job runs, then e6_flight.sh.
# Stops at the first failed flight. Idle checks logged to logs/idle.log.
set -u
E=/home/makerspace/thesis_data/tier1/e6; PROF=$1; shift
for NAME in "$@"; do
  t0=$(date +%s)
  while pgrep -f '[f]igs_' >/dev/null; do
    [ $(( $(date +%s) - t0 )) -gt 7200 ] && { echo "plot job still running after 2 h; not flying $NAME" >&2; exit 2; }
    echo "$(date -Is) waiting before flight $NAME: plot job running" >> $E/logs/idle.log; sleep 30
  done
  echo "$(date -Is) idle ok before flight $NAME (no plot job)" >> $E/logs/idle.log
  echo "$(date -Is) FLIGHT START $NAME" >> $E/logs/flights.log
  bash $E/e6_flight.sh "$NAME" "$PROF" > $E/logs/flight_$NAME.log 2>&1; rc=$?
  echo "$(date -Is) FLIGHT END $NAME rc=$rc" >> $E/logs/flights.log
  [ $rc -ne 0 ] && exit $rc
done
echo "$(date -Is) QUEUE DONE $*" >> $E/logs/flights.log
