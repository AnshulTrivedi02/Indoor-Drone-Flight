#!/usr/bin/env bash
# E6 Stage 1e: map replays on the mapping flights (LC FGO, landmark UKF), serial under heavy.py, from the worktree, then
# eval/e6_maps.py (MAP-INV, map files, map errors). lc_ukf_replay exits 3 by design on a new flight (D75).
set -u
W=/home/makerspace/thesis_ws/.claude/worktrees/agent-afa2971452f4e8507
E=/home/makerspace/thesis_data/tier1/e6; T1=/home/makerspace/thesis_data/tier1
H="python3 $W/src/estimators/fgo_cpp/tools/heavy.py --wait-s 7200"
TS=$E/timing_1e.tsv; mkdir -p $E/logs
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 TBB_NUM_THREADS=1
idle_wait() { local t0=$(date +%s)
  while pgrep -f '[f]igs_' >/dev/null; do [ $(( $(date +%s) - t0 )) -gt 7200 ] && exit 2; echo "$(date -Is) waiting: plot job" >> $E/logs/idle.log; sleep 60; done
  echo "$(date -Is) idle ok before $1" >> $E/logs/idle.log; }
run() { local name=$1; shift; idle_wait "$name"; local s=$(date +%s.%N)
  echo "$(date -Is) START $name" >> $E/logs/driver_1e.log
  ( cd $W && $H "e6 stage1e $name" -- "$@" ) > $E/logs/$name.log 2>&1; local rc=$?; local e=$(date +%s.%N)
  printf '%s\t%s\t%.1f\t%s\n' "$name" "$(date -d @${s%.*} -Is)" "$(echo "$e - $s" | bc)" "$rc" >> $TS
  echo "$(date -Is) END $name rc=$rc" >> $E/logs/driver_1e.log; }
for m in "$@"; do
  run lcfgo_$m /home/makerspace/venv-fgo/bin/python src/estimators/fgo/lc_fgo_replay.py $m --mode lc --t-max 245 --out-root $T1
  run lcukf_$m /home/makerspace/venv-evo/bin/python src/estimators/lc_ukf_replay.py $m --mode lc
  ( cd $W && /home/makerspace/venv-evo/bin/python eval/e6_maps.py $m --fgo-dir $T1/$m/lc_fgo_lc_t245 --ukf-dir $T1/$m/lc_ukf_lc_t245 --out-dir $E/maps/$m ) > $E/logs/maps_$m.log 2>&1
  echo "$(date -Is) MAPS $m rc=$?" >> $E/logs/driver_1e.log
done
echo "$(date -Is) ALL DONE" >> $E/logs/driver_1e.log; touch $E/stage1e.done
