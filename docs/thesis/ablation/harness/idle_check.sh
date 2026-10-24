#!/bin/bash
# Nothing running (pre-registration §9 step 1). Patterns live in this file, so the caller's command line never self-matches.
P='[l]c_fgo_replay|[r]oom_fgo|[f]go_replay|[h]eavy.py|[a]rducopter'
R=$(pgrep -fa "$P" | grep -v "idle_check.sh")
[ -e /home/makerspace/thesis_data/FLIGHT_LOCK ] && { echo "BUSY: FLIGHT_LOCK present"; exit 1; }
[ -n "$R" ] && { echo "BUSY:"; echo "$R"; exit 1; }
echo "IDLE $(date -Iseconds)"; exit 0
