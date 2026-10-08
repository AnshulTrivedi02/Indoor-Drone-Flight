#!/usr/bin/env bash
# Pack every trial bag except experiments T/O/L (T_*, O_*, o_check1), one at a time (ruling 2026-10-08).
# Log: ~/thesis_data/batches/pack_all.log. Stops at the first error. Re-running resumes (packed trials are skipped).
set -u
LOG=~/thesis_data/batches/pack_all.log
for root in ~/thesis_data/trials ~/thesis_data/trials_pre_rerun; do
  for d in "$root"/*/; do
    n=$(basename "$d")
    case "$n" in T_*|O_*|o_check1) echo "$(date -Is) EXCLUDED $n" >> "$LOG"; continue;; esac
    [ -d "$d/bag" ] || { echo "$(date -Is) NOBAG $n" >> "$LOG"; continue; }
    out=$(nice -n 5 "$(dirname "$0")/bag_pack.sh" pack "$d" 2>&1) || { echo "$(date -Is) FAILED $n: $out" >> "$LOG"; echo "FAILED $n"; exit 1; }
    echo "$(date -Is) $out" >> "$LOG"
  done
done
echo "$(date -Is) ALL DONE; free: $(df -h --output=avail ~ | tail -1)" >> "$LOG"
